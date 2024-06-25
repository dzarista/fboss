import json
import sys
from typing import List
from diagrams import Diagram, Cluster, Edge, Node as _Node

class Node():
   def __init__(self, name, shape="record", fillcolor="#5f97e4", **kwargs):
      node_attributes = {
        "label": name,
        "labelloc": "c",
        "shape": shape,
        "width": "2.6",
        "height": "1.6",
        "fixedsize": "true",
        "style": "filled",
        'fontsize': '14',
        "fillcolor": fillcolor,
        "fontcolor": "white",
      }
      node_attributes.update(kwargs)
      self.node = _Node(**node_attributes)

   def getNode(self):
      return self.node


class OutgoingSlotConfigs():
   def __init__(self, slotId, slotType, buses):
      self.slotId = slotId
      self.slotType = slotType
      self.buses = buses

   def renderNode(self):
      buses=""
      for bus in self.buses:
         buses += f"{bus}|"
      buses = buses[:-1]

      if buses:
         label = f" {self.slotId} | {{ {{ {buses} }} }}"
      else:
         label = self.slotId

      height = max( str(2*len(self.buses)), "2")
      self.node = Node(self.slotId, fillcolor="transparent", fontcolor="black",
                       height=height, style="dashed", width="3", label=label ).getNode()


class I2cDeviceConfigs():
   def __init__(self, name, busName, addr):
      self.name = name
      self.busName = busName
      self.addr = addr

   def renderNode(self):
      self.node = Node(f"{{ {self.addr} | {self.name} }}", shape="Mrecord").getNode()


class PciDeviceConfigs():
   def __init__(self, name, vendorId, deviceId, subSysVendorId, subSysDevId, adaps,
                containsXcvrs = False):
      self.name = name
      self.vendorId = vendorId
      self.deviceId = deviceId
      self.subSystemVendorId = subSysVendorId
      self.subSystemDeviceId = subSysDevId
      self.adapters = adaps
      self.containsXcvrs = containsXcvrs

   def renderNode(self):
      vid = f"VID: {self.vendorId}"
      did = f"DID: {self.deviceId}"
      svid = f"SVID: {self.subSystemVendorId}"
      sdid = f"SDID: {self.subSystemDeviceId}"

      label = f" {self.name} | {{ {{{vid} | {did} }}| {{{svid} | {sdid} }} }}"
      self.node = Node(label, fillcolor="#ecf3e7", fontcolor="black", height="3",
                       width="3" ).getNode()


class PmUnit():
   def __init__(self, name, data, parent = None, incomingSlot = None):
      self.data = data
      self.pmUnitConfigs = data["pmUnitConfigs"]
      self.parent: PmUnit = parent
      self.incomingSlot: OutgoingSlotConfigs = incomingSlot
      self.initUnit(name)
      self.exploreSlots()

   def initUnit(self, name):
      pmUnitName = name.split(" ")[0]
      unitConfig = self.pmUnitConfigs[pmUnitName]
      slots = parseSlots(unitConfig["outgoingSlotConfigs"])
      i2cDevices = parseI2cDevices(unitConfig["i2cDeviceConfigs"])
      pciConfigs = parsePci(unitConfig["pciDeviceConfigs"]) 
      self.initUnitData(name, slots, i2cDevices, pciConfigs)

   def initUnitData(self, name, slots, devices, pciConfigs):
      self.name = name
      self.isRoot = self.parent is None
      self.slots:List[OutgoingSlotConfigs] = slots
      self.i2cDevices: List[I2cDeviceConfigs] = devices
      self.pciConfigs: List[PciDeviceConfigs] = pciConfigs
      self.pmUnits: List[PmUnit] = []

   def exploreSlots(self):
      if not self.slots:
         return
        
      for slot in self.slots:
         name = self.data["slotTypeConfigs"][slot.slotType]["pmUnitName"]

         if name in ("FAN", "PSU"):
            name = f"{name} {int(slot.slotId[-1])+1}"

         unit = PmUnit(name, self.data, self, slot)
         self.pmUnits.append(unit)

   def renderCluster(self):
      # NOTE: FANs are handled as a special case since they don't contain any 
      # incoming/outgoing buses
      with Cluster(f"PmUnit - {self.name} {'(Root)' if not self.parent else ''}",
                   graph_attr={"rankdir":"TB", 'fontsize': '24'}):
         
         if self.isRoot:
            with Cluster("CPU"):
               #TODO: render dynamically once supported
               Node("CPU_CORE_TEMP").getNode()

         for slot in self.slots:
            slot.renderNode()

         with Cluster("I2C devices"):
            for i2cDev in self.i2cDevices:
               i2cDev.renderNode()
               # This handles the FAN_CPLD to Fans relationship
               if i2cDev.name == "FAN_CPLD":
                  for slot in self.slots:
                     if slot.slotType == "FAN_SLOT":
                        attrs = {}
                        i2cDev.node - Edge(style="dashed", **attrs) - slot.node  

         for pciDev in self.pciConfigs:
            pciDev.renderNode()
            for i2cDev in self.i2cDevices:
               thisBus = i2cDev.busName.split("@")[0]
               if thisBus in pciDev.adapters:
                  attrs = {
                     "minlen":"2",
                     "headlabel":i2cDev.busName
                  }
                  pciDev.node >> Edge(**attrs) >> i2cDev.node

            for slot in self.slots:
               if slot.buses:
                  attrs = {
                     "minlen":"3",
                  }
                  pciDev.node - Edge(**attrs) - slot.node

            if pciDev.containsXcvrs:
               xcvrNode = Node("XCVRs").getNode()
               attrs = {
                  "minlen":"0",
               }
               pciDev.node >> Edge(**attrs) >> xcvrNode

         if self.incomingSlot:
            for i2cDev in self.i2cDevices:
               if i2cDev.busName.split("@")[0] == "INCOMING":
                  attrs = {
                     "minlen": "3",
                  }
                  self.incomingSlot.node >> \
                     Edge(label=i2cDev.busName, **attrs) >> i2cDev.node

            if "FAN" in self.name and len(self.i2cDevices) == 0:
               attrs = {
                  "minlen": "3",
               }   
               self.incomingSlot.node - Edge(style="dashed", **attrs) \
                  >> Node("FAN").getNode()

   def render(self):
      self.renderCluster()
        
      for unit in self.pmUnits:
         unit.render()


def parseSlots(outgoingSlotConfigs) -> List[OutgoingSlotConfigs] :
   slots = []
   for slotId, slot in outgoingSlotConfigs.items():
      slotType = slot["slotType"]
      buses = slot["outgoingI2cBusNames"]
      s = OutgoingSlotConfigs(slotId, slotType, buses)
      slots.append(s)
   return slots


def parseI2cDevices(i2cDeviceConfigs) -> List[I2cDeviceConfigs]:
   i2cDevices = []
   for i2cDevice in i2cDeviceConfigs:
      name = i2cDevice["pmUnitScopedName"]
      bus = i2cDevice["busName"]
      addr = i2cDevice["address"]
      d = I2cDeviceConfigs(name, bus, addr)
      i2cDevices.append(d)
   return i2cDevices


def parsePci(pciDeviceConfigs) -> PciDeviceConfigs:
   pciDevs = []
   for pciDev in pciDeviceConfigs:
      name = pciDev["pmUnitScopedName"]
      venId = pciDev["vendorId"]
      devId = pciDev["deviceId"]
      subSysVenId = pciDev["subSystemVendorId"]
      subSysDevId = pciDev["subSystemDeviceId"]

      adaps = []
      for adapter in pciDev["i2cAdapterConfigs"]:
         adapName = adapter["fpgaIpBlockConfig"]["pmUnitScopedName"]
         adaps.append(adapName)

      containsXcvrs = len(pciDev["xcvrCtrlConfigs"]) > 0
      pciDevs.append(PciDeviceConfigs(name, venId, devId, subSysVenId, subSysDevId,
                                      adaps, containsXcvrs))
   return pciDevs


def printPmUnitTree(root, depth=0):
   '''
   Helper function to view the platform as a tree of PMUnits
   e.g.
   SCM
   SMB
      PSU1
      PSU2
      FAN1
      FAN2
   '''
   print('\t' * depth + root.name)

   for unit in root.pmUnits:
      printPmUnitTree(unit, depth + 1)


def genDiagram(data):
   platformName = data['platformName']
   root = PmUnit(data["rootPmUnitName"], data)
   graph_attr = {
      "ratio": "0.5625",
      'rankdir': 'LR',
      'show': 'False',
      'fontsize': '36'
   }
   with Diagram(f"Platform: {platformName}", show=False, graph_attr=graph_attr):
      root.render()


def main():
   if len( sys.argv ) < 2:
      print( f'Usage: {sys.argv[ 0 ]} <FILE.json>' )
      sys.exit( 1 )

   jsonFile = sys.argv[ 1 ]

   with open(jsonFile, 'r') as file:
      data = json.load(file)

   genDiagram(data)


if __name__ == '__main__':
   main()