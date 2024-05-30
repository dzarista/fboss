# Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

# XXX_seerpini imported from
# diags.dev-base-trunk-dmz/src/DosSand/DosBoard/WhistlerP1LanesMappingData.py and
# modified to only retain the logical lane maps and the trace length information.


# Fake Fe and CoreData definitions to be able to import trace lengths in
# wireAndApplyPolTraceLen() below which is imported from diags code.
# Diags uses this code to populate their internal Fe objects, which we don't have to
# replicate/use in full here.
class Fe:
   class CoreData:
      class LaneData:
         traceLengthToNextEpInInches: float
         doRxPolaritySwapped : bool
         doTxPolaritySwapped : bool
      lanes : list[ LaneData ]
      def __init__( self, numLanes ):
         self.lanes = [ self.LaneData() for i in range( numLanes )  ]
   cores : list[ CoreData ]
   def __init__( self, numCores, numLanesPerCore ):
         self.cores = [ self.CoreData( numLanesPerCore ) for i in range( numCores ) ]

# Due to the 2x2 mux on Ramon3, we have a weird mapping between the logical lanes on
# the ASIC and the per core lanes used in the information below. Each serdes core is
# mapped to both the VDs and the per core logical lane is swapped when VD0 is
# connected to the second quartet in a core and VD1 is connected to the first
# quartet in a core.
# It translates to the following scheme assuming 256 logical lanes per Virtual
# Device (VD) and 8 lanes per serdes core.
def logicalLaneToPhysicalCoreLogicalLane( asicLogicalLane: int,
                                          physicalSerdes: int ) -> int:
   assert physicalSerdes < 512 # 2 VDs per ASIC with 256 lanes each
   perCoreLogicalLane = physicalSerdes % 8
   vd = 0 if asicLogicalLane < 256 else 1
   if vd == 0:
      if perCoreLogicalLane >= 4:
         perCoreLogicalLane -= 4
   else:
      if perCoreLogicalLane < 4:
         perCoreLogicalLane += 4
   return perCoreLogicalLane

def fabricTraceLengthByLogicalLane( numCoresPerAsic: int,
                                    numLanesPerCore : int ) -> list[ Fe ]:
   assert numCoresPerAsic == 64
   assert numLanesPerCore == 8
   fes = [ Fe( numCoresPerAsic, numLanesPerCore ) for i in range( 2 ) ]
   wireAndApplyPolTraceLen(fes)
   return fes

# this data is generated using Dos/utils/parseWhistlerNets.py
# python -i ./parseWhistlerNets.py --file whistler_p1_pinPairReport.csv
# generateSocProps()
feToLaneMapSocProps = [
   { # fe0
      'lane_to_serdes_map_fabric_lane0': 'rx4:tx5',
      'lane_to_serdes_map_fabric_lane1': 'rx5:tx4',
      'lane_to_serdes_map_fabric_lane2': 'rx2:tx3',
      'lane_to_serdes_map_fabric_lane3': 'rx3:tx2',
      'lane_to_serdes_map_fabric_lane256': 'rx0:tx1',
      'lane_to_serdes_map_fabric_lane257': 'rx1:tx0',
      'lane_to_serdes_map_fabric_lane258': 'rx6:tx7',
      'lane_to_serdes_map_fabric_lane259': 'rx7:tx6',
      'lane_to_serdes_map_fabric_lane4': 'rx8:tx9',
      'lane_to_serdes_map_fabric_lane5': 'rx9:tx8',
      'lane_to_serdes_map_fabric_lane6': 'rx14:tx15',
      'lane_to_serdes_map_fabric_lane7': 'rx15:tx14',
      'lane_to_serdes_map_fabric_lane260': 'rx12:tx13',
      'lane_to_serdes_map_fabric_lane261': 'rx13:tx12',
      'lane_to_serdes_map_fabric_lane262': 'rx10:tx11',
      'lane_to_serdes_map_fabric_lane263': 'rx11:tx10',
      'lane_to_serdes_map_fabric_lane8': 'rx20:tx20',
      'lane_to_serdes_map_fabric_lane9': 'rx21:tx21',
      'lane_to_serdes_map_fabric_lane10': 'rx18:tx18',
      'lane_to_serdes_map_fabric_lane11': 'rx19:tx19',
      'lane_to_serdes_map_fabric_lane264': 'rx16:tx16',
      'lane_to_serdes_map_fabric_lane265': 'rx17:tx17',
      'lane_to_serdes_map_fabric_lane266': 'rx22:tx22',
      'lane_to_serdes_map_fabric_lane267': 'rx23:tx23',
      'lane_to_serdes_map_fabric_lane12': 'rx24:tx24',
      'lane_to_serdes_map_fabric_lane13': 'rx25:tx25',
      'lane_to_serdes_map_fabric_lane14': 'rx30:tx30',
      'lane_to_serdes_map_fabric_lane15': 'rx31:tx31',
      'lane_to_serdes_map_fabric_lane268': 'rx28:tx28',
      'lane_to_serdes_map_fabric_lane269': 'rx29:tx29',
      'lane_to_serdes_map_fabric_lane270': 'rx26:tx26',
      'lane_to_serdes_map_fabric_lane271': 'rx27:tx27',
      'lane_to_serdes_map_fabric_lane16': 'rx36:tx39',
      'lane_to_serdes_map_fabric_lane17': 'rx37:tx36',
      'lane_to_serdes_map_fabric_lane18': 'rx34:tx33',
      'lane_to_serdes_map_fabric_lane19': 'rx35:tx34',
      'lane_to_serdes_map_fabric_lane272': 'rx32:tx35',
      'lane_to_serdes_map_fabric_lane273': 'rx33:tx32',
      'lane_to_serdes_map_fabric_lane274': 'rx38:tx37',
      'lane_to_serdes_map_fabric_lane275': 'rx39:tx38',
      'lane_to_serdes_map_fabric_lane20': 'rx40:tx47',
      'lane_to_serdes_map_fabric_lane21': 'rx41:tx44',
      'lane_to_serdes_map_fabric_lane22': 'rx46:tx41',
      'lane_to_serdes_map_fabric_lane23': 'rx47:tx42',
      'lane_to_serdes_map_fabric_lane276': 'rx44:tx43',
      'lane_to_serdes_map_fabric_lane277': 'rx45:tx40',
      'lane_to_serdes_map_fabric_lane278': 'rx42:tx45',
      'lane_to_serdes_map_fabric_lane279': 'rx43:tx46',
      'lane_to_serdes_map_fabric_lane24': 'rx48:tx52',
      'lane_to_serdes_map_fabric_lane25': 'rx49:tx53',
      'lane_to_serdes_map_fabric_lane26': 'rx54:tx50',
      'lane_to_serdes_map_fabric_lane27': 'rx55:tx51',
      'lane_to_serdes_map_fabric_lane280': 'rx52:tx48',
      'lane_to_serdes_map_fabric_lane281': 'rx53:tx49',
      'lane_to_serdes_map_fabric_lane282': 'rx50:tx54',
      'lane_to_serdes_map_fabric_lane283': 'rx51:tx55',
      'lane_to_serdes_map_fabric_lane28': 'rx56:tx60',
      'lane_to_serdes_map_fabric_lane29': 'rx57:tx61',
      'lane_to_serdes_map_fabric_lane30': 'rx62:tx58',
      'lane_to_serdes_map_fabric_lane31': 'rx63:tx59',
      'lane_to_serdes_map_fabric_lane284': 'rx60:tx56',
      'lane_to_serdes_map_fabric_lane285': 'rx61:tx57',
      'lane_to_serdes_map_fabric_lane286': 'rx58:tx62',
      'lane_to_serdes_map_fabric_lane287': 'rx59:tx63',
      'lane_to_serdes_map_fabric_lane32': 'rx64:tx71',
      'lane_to_serdes_map_fabric_lane33': 'rx65:tx68',
      'lane_to_serdes_map_fabric_lane34': 'rx70:tx65',
      'lane_to_serdes_map_fabric_lane35': 'rx71:tx66',
      'lane_to_serdes_map_fabric_lane288': 'rx68:tx67',
      'lane_to_serdes_map_fabric_lane289': 'rx69:tx64',
      'lane_to_serdes_map_fabric_lane290': 'rx66:tx69',
      'lane_to_serdes_map_fabric_lane291': 'rx67:tx70',
      'lane_to_serdes_map_fabric_lane36': 'rx72:tx79',
      'lane_to_serdes_map_fabric_lane37': 'rx73:tx76',
      'lane_to_serdes_map_fabric_lane38': 'rx78:tx73',
      'lane_to_serdes_map_fabric_lane39': 'rx79:tx74',
      'lane_to_serdes_map_fabric_lane292': 'rx76:tx75',
      'lane_to_serdes_map_fabric_lane293': 'rx77:tx72',
      'lane_to_serdes_map_fabric_lane294': 'rx74:tx77',
      'lane_to_serdes_map_fabric_lane295': 'rx75:tx78',
      'lane_to_serdes_map_fabric_lane40': 'rx80:tx84',
      'lane_to_serdes_map_fabric_lane41': 'rx81:tx85',
      'lane_to_serdes_map_fabric_lane42': 'rx86:tx82',
      'lane_to_serdes_map_fabric_lane43': 'rx87:tx83',
      'lane_to_serdes_map_fabric_lane296': 'rx84:tx80',
      'lane_to_serdes_map_fabric_lane297': 'rx85:tx81',
      'lane_to_serdes_map_fabric_lane298': 'rx82:tx86',
      'lane_to_serdes_map_fabric_lane299': 'rx83:tx87',
      'lane_to_serdes_map_fabric_lane44': 'rx88:tx92',
      'lane_to_serdes_map_fabric_lane45': 'rx89:tx93',
      'lane_to_serdes_map_fabric_lane46': 'rx94:tx90',
      'lane_to_serdes_map_fabric_lane47': 'rx95:tx91',
      'lane_to_serdes_map_fabric_lane300': 'rx92:tx88',
      'lane_to_serdes_map_fabric_lane301': 'rx93:tx89',
      'lane_to_serdes_map_fabric_lane302': 'rx90:tx94',
      'lane_to_serdes_map_fabric_lane303': 'rx91:tx95',
      'lane_to_serdes_map_fabric_lane48': 'rx96:tx103',
      'lane_to_serdes_map_fabric_lane49': 'rx97:tx100',
      'lane_to_serdes_map_fabric_lane50': 'rx102:tx97',
      'lane_to_serdes_map_fabric_lane51': 'rx103:tx98',
      'lane_to_serdes_map_fabric_lane304': 'rx100:tx99',
      'lane_to_serdes_map_fabric_lane305': 'rx101:tx96',
      'lane_to_serdes_map_fabric_lane306': 'rx98:tx101',
      'lane_to_serdes_map_fabric_lane307': 'rx99:tx102',
      'lane_to_serdes_map_fabric_lane52': 'rx104:tx111',
      'lane_to_serdes_map_fabric_lane53': 'rx105:tx108',
      'lane_to_serdes_map_fabric_lane54': 'rx110:tx105',
      'lane_to_serdes_map_fabric_lane55': 'rx111:tx106',
      'lane_to_serdes_map_fabric_lane308': 'rx108:tx107',
      'lane_to_serdes_map_fabric_lane309': 'rx109:tx104',
      'lane_to_serdes_map_fabric_lane310': 'rx106:tx109',
      'lane_to_serdes_map_fabric_lane311': 'rx107:tx110',
      'lane_to_serdes_map_fabric_lane56': 'rx112:tx116',
      'lane_to_serdes_map_fabric_lane57': 'rx113:tx117',
      'lane_to_serdes_map_fabric_lane58': 'rx118:tx114',
      'lane_to_serdes_map_fabric_lane59': 'rx119:tx115',
      'lane_to_serdes_map_fabric_lane312': 'rx116:tx112',
      'lane_to_serdes_map_fabric_lane313': 'rx117:tx113',
      'lane_to_serdes_map_fabric_lane314': 'rx114:tx118',
      'lane_to_serdes_map_fabric_lane315': 'rx115:tx119',
      'lane_to_serdes_map_fabric_lane60': 'rx120:tx124',
      'lane_to_serdes_map_fabric_lane61': 'rx121:tx125',
      'lane_to_serdes_map_fabric_lane62': 'rx126:tx122',
      'lane_to_serdes_map_fabric_lane63': 'rx127:tx123',
      'lane_to_serdes_map_fabric_lane316': 'rx124:tx120',
      'lane_to_serdes_map_fabric_lane317': 'rx125:tx121',
      'lane_to_serdes_map_fabric_lane318': 'rx122:tx126',
      'lane_to_serdes_map_fabric_lane319': 'rx123:tx127',
      'lane_to_serdes_map_fabric_lane64': 'rx132:tx131',
      'lane_to_serdes_map_fabric_lane65': 'rx133:tx128',
      'lane_to_serdes_map_fabric_lane66': 'rx130:tx133',
      'lane_to_serdes_map_fabric_lane67': 'rx131:tx134',
      'lane_to_serdes_map_fabric_lane320': 'rx128:tx135',
      'lane_to_serdes_map_fabric_lane321': 'rx129:tx132',
      'lane_to_serdes_map_fabric_lane322': 'rx134:tx129',
      'lane_to_serdes_map_fabric_lane323': 'rx135:tx130',
      'lane_to_serdes_map_fabric_lane68': 'rx140:tx139',
      'lane_to_serdes_map_fabric_lane69': 'rx141:tx136',
      'lane_to_serdes_map_fabric_lane70': 'rx138:tx141',
      'lane_to_serdes_map_fabric_lane71': 'rx139:tx142',
      'lane_to_serdes_map_fabric_lane324': 'rx136:tx143',
      'lane_to_serdes_map_fabric_lane325': 'rx137:tx140',
      'lane_to_serdes_map_fabric_lane326': 'rx142:tx137',
      'lane_to_serdes_map_fabric_lane327': 'rx143:tx138',
      'lane_to_serdes_map_fabric_lane72': 'rx148:tx144',
      'lane_to_serdes_map_fabric_lane73': 'rx149:tx145',
      'lane_to_serdes_map_fabric_lane74': 'rx146:tx150',
      'lane_to_serdes_map_fabric_lane75': 'rx147:tx151',
      'lane_to_serdes_map_fabric_lane328': 'rx144:tx148',
      'lane_to_serdes_map_fabric_lane329': 'rx145:tx149',
      'lane_to_serdes_map_fabric_lane330': 'rx150:tx146',
      'lane_to_serdes_map_fabric_lane331': 'rx151:tx147',
      'lane_to_serdes_map_fabric_lane76': 'rx156:tx152',
      'lane_to_serdes_map_fabric_lane77': 'rx157:tx153',
      'lane_to_serdes_map_fabric_lane78': 'rx154:tx158',
      'lane_to_serdes_map_fabric_lane79': 'rx155:tx159',
      'lane_to_serdes_map_fabric_lane332': 'rx152:tx156',
      'lane_to_serdes_map_fabric_lane333': 'rx153:tx157',
      'lane_to_serdes_map_fabric_lane334': 'rx158:tx154',
      'lane_to_serdes_map_fabric_lane335': 'rx159:tx155',
      'lane_to_serdes_map_fabric_lane80': 'rx164:tx163',
      'lane_to_serdes_map_fabric_lane81': 'rx165:tx160',
      'lane_to_serdes_map_fabric_lane82': 'rx162:tx165',
      'lane_to_serdes_map_fabric_lane83': 'rx163:tx166',
      'lane_to_serdes_map_fabric_lane336': 'rx160:tx167',
      'lane_to_serdes_map_fabric_lane337': 'rx161:tx164',
      'lane_to_serdes_map_fabric_lane338': 'rx166:tx161',
      'lane_to_serdes_map_fabric_lane339': 'rx167:tx162',
      'lane_to_serdes_map_fabric_lane84': 'rx172:tx171',
      'lane_to_serdes_map_fabric_lane85': 'rx173:tx168',
      'lane_to_serdes_map_fabric_lane86': 'rx170:tx173',
      'lane_to_serdes_map_fabric_lane87': 'rx171:tx174',
      'lane_to_serdes_map_fabric_lane340': 'rx168:tx175',
      'lane_to_serdes_map_fabric_lane341': 'rx169:tx172',
      'lane_to_serdes_map_fabric_lane342': 'rx174:tx169',
      'lane_to_serdes_map_fabric_lane343': 'rx175:tx170',
      'lane_to_serdes_map_fabric_lane88': 'rx180:tx176',
      'lane_to_serdes_map_fabric_lane89': 'rx181:tx177',
      'lane_to_serdes_map_fabric_lane90': 'rx178:tx182',
      'lane_to_serdes_map_fabric_lane91': 'rx179:tx183',
      'lane_to_serdes_map_fabric_lane344': 'rx176:tx180',
      'lane_to_serdes_map_fabric_lane345': 'rx177:tx181',
      'lane_to_serdes_map_fabric_lane346': 'rx182:tx178',
      'lane_to_serdes_map_fabric_lane347': 'rx183:tx179',
      'lane_to_serdes_map_fabric_lane92': 'rx188:tx184',
      'lane_to_serdes_map_fabric_lane93': 'rx189:tx185',
      'lane_to_serdes_map_fabric_lane94': 'rx186:tx190',
      'lane_to_serdes_map_fabric_lane95': 'rx187:tx191',
      'lane_to_serdes_map_fabric_lane348': 'rx184:tx188',
      'lane_to_serdes_map_fabric_lane349': 'rx185:tx189',
      'lane_to_serdes_map_fabric_lane350': 'rx190:tx186',
      'lane_to_serdes_map_fabric_lane351': 'rx191:tx187',
      'lane_to_serdes_map_fabric_lane96': 'rx196:tx195',
      'lane_to_serdes_map_fabric_lane97': 'rx197:tx192',
      'lane_to_serdes_map_fabric_lane98': 'rx194:tx197',
      'lane_to_serdes_map_fabric_lane99': 'rx195:tx198',
      'lane_to_serdes_map_fabric_lane352': 'rx192:tx199',
      'lane_to_serdes_map_fabric_lane353': 'rx193:tx196',
      'lane_to_serdes_map_fabric_lane354': 'rx198:tx193',
      'lane_to_serdes_map_fabric_lane355': 'rx199:tx194',
      'lane_to_serdes_map_fabric_lane100': 'rx204:tx203',
      'lane_to_serdes_map_fabric_lane101': 'rx205:tx200',
      'lane_to_serdes_map_fabric_lane102': 'rx202:tx205',
      'lane_to_serdes_map_fabric_lane103': 'rx203:tx206',
      'lane_to_serdes_map_fabric_lane356': 'rx200:tx207',
      'lane_to_serdes_map_fabric_lane357': 'rx201:tx204',
      'lane_to_serdes_map_fabric_lane358': 'rx206:tx201',
      'lane_to_serdes_map_fabric_lane359': 'rx207:tx202',
      'lane_to_serdes_map_fabric_lane104': 'rx212:tx208',
      'lane_to_serdes_map_fabric_lane105': 'rx213:tx209',
      'lane_to_serdes_map_fabric_lane106': 'rx210:tx214',
      'lane_to_serdes_map_fabric_lane107': 'rx211:tx215',
      'lane_to_serdes_map_fabric_lane360': 'rx208:tx212',
      'lane_to_serdes_map_fabric_lane361': 'rx209:tx213',
      'lane_to_serdes_map_fabric_lane362': 'rx214:tx210',
      'lane_to_serdes_map_fabric_lane363': 'rx215:tx211',
      'lane_to_serdes_map_fabric_lane108': 'rx220:tx216',
      'lane_to_serdes_map_fabric_lane109': 'rx221:tx217',
      'lane_to_serdes_map_fabric_lane110': 'rx218:tx222',
      'lane_to_serdes_map_fabric_lane111': 'rx219:tx223',
      'lane_to_serdes_map_fabric_lane364': 'rx216:tx220',
      'lane_to_serdes_map_fabric_lane365': 'rx217:tx221',
      'lane_to_serdes_map_fabric_lane366': 'rx222:tx218',
      'lane_to_serdes_map_fabric_lane367': 'rx223:tx219',
      'lane_to_serdes_map_fabric_lane112': 'rx228:tx229',
      'lane_to_serdes_map_fabric_lane113': 'rx229:tx228',
      'lane_to_serdes_map_fabric_lane114': 'rx226:tx227',
      'lane_to_serdes_map_fabric_lane115': 'rx227:tx226',
      'lane_to_serdes_map_fabric_lane368': 'rx224:tx225',
      'lane_to_serdes_map_fabric_lane369': 'rx225:tx224',
      'lane_to_serdes_map_fabric_lane370': 'rx230:tx231',
      'lane_to_serdes_map_fabric_lane371': 'rx231:tx230',
      'lane_to_serdes_map_fabric_lane116': 'rx232:tx233',
      'lane_to_serdes_map_fabric_lane117': 'rx233:tx232',
      'lane_to_serdes_map_fabric_lane118': 'rx238:tx239',
      'lane_to_serdes_map_fabric_lane119': 'rx239:tx238',
      'lane_to_serdes_map_fabric_lane372': 'rx236:tx237',
      'lane_to_serdes_map_fabric_lane373': 'rx237:tx236',
      'lane_to_serdes_map_fabric_lane374': 'rx234:tx235',
      'lane_to_serdes_map_fabric_lane375': 'rx235:tx234',
      'lane_to_serdes_map_fabric_lane120': 'rx244:tx244',
      'lane_to_serdes_map_fabric_lane121': 'rx245:tx245',
      'lane_to_serdes_map_fabric_lane122': 'rx242:tx242',
      'lane_to_serdes_map_fabric_lane123': 'rx243:tx243',
      'lane_to_serdes_map_fabric_lane376': 'rx240:tx240',
      'lane_to_serdes_map_fabric_lane377': 'rx241:tx241',
      'lane_to_serdes_map_fabric_lane378': 'rx246:tx246',
      'lane_to_serdes_map_fabric_lane379': 'rx247:tx247',
      'lane_to_serdes_map_fabric_lane124': 'rx248:tx248',
      'lane_to_serdes_map_fabric_lane125': 'rx249:tx249',
      'lane_to_serdes_map_fabric_lane126': 'rx254:tx254',
      'lane_to_serdes_map_fabric_lane127': 'rx255:tx255',
      'lane_to_serdes_map_fabric_lane380': 'rx252:tx252',
      'lane_to_serdes_map_fabric_lane381': 'rx253:tx253',
      'lane_to_serdes_map_fabric_lane382': 'rx250:tx250',
      'lane_to_serdes_map_fabric_lane383': 'rx251:tx251',
      'lane_to_serdes_map_fabric_lane128': 'rx256:tx257',
      'lane_to_serdes_map_fabric_lane129': 'rx257:tx256',
      'lane_to_serdes_map_fabric_lane130': 'rx262:tx263',
      'lane_to_serdes_map_fabric_lane131': 'rx263:tx262',
      'lane_to_serdes_map_fabric_lane384': 'rx260:tx261',
      'lane_to_serdes_map_fabric_lane385': 'rx261:tx260',
      'lane_to_serdes_map_fabric_lane386': 'rx258:tx259',
      'lane_to_serdes_map_fabric_lane387': 'rx259:tx258',
      'lane_to_serdes_map_fabric_lane132': 'rx268:tx269',
      'lane_to_serdes_map_fabric_lane133': 'rx269:tx268',
      'lane_to_serdes_map_fabric_lane134': 'rx266:tx267',
      'lane_to_serdes_map_fabric_lane135': 'rx267:tx266',
      'lane_to_serdes_map_fabric_lane388': 'rx264:tx265',
      'lane_to_serdes_map_fabric_lane389': 'rx265:tx264',
      'lane_to_serdes_map_fabric_lane390': 'rx270:tx271',
      'lane_to_serdes_map_fabric_lane391': 'rx271:tx270',
      'lane_to_serdes_map_fabric_lane136': 'rx272:tx272',
      'lane_to_serdes_map_fabric_lane137': 'rx273:tx273',
      'lane_to_serdes_map_fabric_lane138': 'rx278:tx278',
      'lane_to_serdes_map_fabric_lane139': 'rx279:tx279',
      'lane_to_serdes_map_fabric_lane392': 'rx276:tx276',
      'lane_to_serdes_map_fabric_lane393': 'rx277:tx277',
      'lane_to_serdes_map_fabric_lane394': 'rx274:tx274',
      'lane_to_serdes_map_fabric_lane395': 'rx275:tx275',
      'lane_to_serdes_map_fabric_lane140': 'rx284:tx284',
      'lane_to_serdes_map_fabric_lane141': 'rx285:tx285',
      'lane_to_serdes_map_fabric_lane142': 'rx282:tx282',
      'lane_to_serdes_map_fabric_lane143': 'rx283:tx283',
      'lane_to_serdes_map_fabric_lane396': 'rx280:tx280',
      'lane_to_serdes_map_fabric_lane397': 'rx281:tx281',
      'lane_to_serdes_map_fabric_lane398': 'rx286:tx286',
      'lane_to_serdes_map_fabric_lane399': 'rx287:tx287',
      'lane_to_serdes_map_fabric_lane144': 'rx288:tx295',
      'lane_to_serdes_map_fabric_lane145': 'rx289:tx292',
      'lane_to_serdes_map_fabric_lane146': 'rx294:tx289',
      'lane_to_serdes_map_fabric_lane147': 'rx295:tx290',
      'lane_to_serdes_map_fabric_lane400': 'rx292:tx291',
      'lane_to_serdes_map_fabric_lane401': 'rx293:tx288',
      'lane_to_serdes_map_fabric_lane402': 'rx290:tx293',
      'lane_to_serdes_map_fabric_lane403': 'rx291:tx294',
      'lane_to_serdes_map_fabric_lane148': 'rx296:tx303',
      'lane_to_serdes_map_fabric_lane149': 'rx297:tx300',
      'lane_to_serdes_map_fabric_lane150': 'rx302:tx297',
      'lane_to_serdes_map_fabric_lane151': 'rx303:tx298',
      'lane_to_serdes_map_fabric_lane404': 'rx300:tx299',
      'lane_to_serdes_map_fabric_lane405': 'rx301:tx296',
      'lane_to_serdes_map_fabric_lane406': 'rx298:tx301',
      'lane_to_serdes_map_fabric_lane407': 'rx299:tx302',
      'lane_to_serdes_map_fabric_lane152': 'rx304:tx308',
      'lane_to_serdes_map_fabric_lane153': 'rx305:tx309',
      'lane_to_serdes_map_fabric_lane154': 'rx310:tx306',
      'lane_to_serdes_map_fabric_lane155': 'rx311:tx307',
      'lane_to_serdes_map_fabric_lane408': 'rx308:tx304',
      'lane_to_serdes_map_fabric_lane409': 'rx309:tx305',
      'lane_to_serdes_map_fabric_lane410': 'rx306:tx310',
      'lane_to_serdes_map_fabric_lane411': 'rx307:tx311',
      'lane_to_serdes_map_fabric_lane156': 'rx312:tx316',
      'lane_to_serdes_map_fabric_lane157': 'rx313:tx317',
      'lane_to_serdes_map_fabric_lane158': 'rx318:tx314',
      'lane_to_serdes_map_fabric_lane159': 'rx319:tx315',
      'lane_to_serdes_map_fabric_lane412': 'rx316:tx312',
      'lane_to_serdes_map_fabric_lane413': 'rx317:tx313',
      'lane_to_serdes_map_fabric_lane414': 'rx314:tx318',
      'lane_to_serdes_map_fabric_lane415': 'rx315:tx319',
      'lane_to_serdes_map_fabric_lane160': 'rx320:tx327',
      'lane_to_serdes_map_fabric_lane161': 'rx321:tx324',
      'lane_to_serdes_map_fabric_lane162': 'rx326:tx321',
      'lane_to_serdes_map_fabric_lane163': 'rx327:tx322',
      'lane_to_serdes_map_fabric_lane416': 'rx324:tx323',
      'lane_to_serdes_map_fabric_lane417': 'rx325:tx320',
      'lane_to_serdes_map_fabric_lane418': 'rx322:tx325',
      'lane_to_serdes_map_fabric_lane419': 'rx323:tx326',
      'lane_to_serdes_map_fabric_lane164': 'rx328:tx335',
      'lane_to_serdes_map_fabric_lane165': 'rx329:tx332',
      'lane_to_serdes_map_fabric_lane166': 'rx334:tx329',
      'lane_to_serdes_map_fabric_lane167': 'rx335:tx330',
      'lane_to_serdes_map_fabric_lane420': 'rx332:tx331',
      'lane_to_serdes_map_fabric_lane421': 'rx333:tx328',
      'lane_to_serdes_map_fabric_lane422': 'rx330:tx333',
      'lane_to_serdes_map_fabric_lane423': 'rx331:tx334',
      'lane_to_serdes_map_fabric_lane168': 'rx336:tx340',
      'lane_to_serdes_map_fabric_lane169': 'rx337:tx341',
      'lane_to_serdes_map_fabric_lane170': 'rx342:tx338',
      'lane_to_serdes_map_fabric_lane171': 'rx343:tx339',
      'lane_to_serdes_map_fabric_lane424': 'rx340:tx336',
      'lane_to_serdes_map_fabric_lane425': 'rx341:tx337',
      'lane_to_serdes_map_fabric_lane426': 'rx338:tx342',
      'lane_to_serdes_map_fabric_lane427': 'rx339:tx343',
      'lane_to_serdes_map_fabric_lane172': 'rx344:tx348',
      'lane_to_serdes_map_fabric_lane173': 'rx345:tx349',
      'lane_to_serdes_map_fabric_lane174': 'rx350:tx346',
      'lane_to_serdes_map_fabric_lane175': 'rx351:tx347',
      'lane_to_serdes_map_fabric_lane428': 'rx348:tx344',
      'lane_to_serdes_map_fabric_lane429': 'rx349:tx345',
      'lane_to_serdes_map_fabric_lane430': 'rx346:tx350',
      'lane_to_serdes_map_fabric_lane431': 'rx347:tx351',
      'lane_to_serdes_map_fabric_lane176': 'rx352:tx359',
      'lane_to_serdes_map_fabric_lane177': 'rx353:tx356',
      'lane_to_serdes_map_fabric_lane178': 'rx358:tx353',
      'lane_to_serdes_map_fabric_lane179': 'rx359:tx354',
      'lane_to_serdes_map_fabric_lane432': 'rx356:tx355',
      'lane_to_serdes_map_fabric_lane433': 'rx357:tx352',
      'lane_to_serdes_map_fabric_lane434': 'rx354:tx357',
      'lane_to_serdes_map_fabric_lane435': 'rx355:tx358',
      'lane_to_serdes_map_fabric_lane180': 'rx360:tx367',
      'lane_to_serdes_map_fabric_lane181': 'rx361:tx364',
      'lane_to_serdes_map_fabric_lane182': 'rx366:tx361',
      'lane_to_serdes_map_fabric_lane183': 'rx367:tx362',
      'lane_to_serdes_map_fabric_lane436': 'rx364:tx363',
      'lane_to_serdes_map_fabric_lane437': 'rx365:tx360',
      'lane_to_serdes_map_fabric_lane438': 'rx362:tx365',
      'lane_to_serdes_map_fabric_lane439': 'rx363:tx366',
      'lane_to_serdes_map_fabric_lane184': 'rx368:tx372',
      'lane_to_serdes_map_fabric_lane185': 'rx369:tx373',
      'lane_to_serdes_map_fabric_lane186': 'rx374:tx370',
      'lane_to_serdes_map_fabric_lane187': 'rx375:tx371',
      'lane_to_serdes_map_fabric_lane440': 'rx372:tx368',
      'lane_to_serdes_map_fabric_lane441': 'rx373:tx369',
      'lane_to_serdes_map_fabric_lane442': 'rx370:tx374',
      'lane_to_serdes_map_fabric_lane443': 'rx371:tx375',
      'lane_to_serdes_map_fabric_lane188': 'rx376:tx380',
      'lane_to_serdes_map_fabric_lane189': 'rx377:tx381',
      'lane_to_serdes_map_fabric_lane190': 'rx382:tx378',
      'lane_to_serdes_map_fabric_lane191': 'rx383:tx379',
      'lane_to_serdes_map_fabric_lane444': 'rx380:tx376',
      'lane_to_serdes_map_fabric_lane445': 'rx381:tx377',
      'lane_to_serdes_map_fabric_lane446': 'rx378:tx382',
      'lane_to_serdes_map_fabric_lane447': 'rx379:tx383',
      'lane_to_serdes_map_fabric_lane192': 'rx388:tx387',
      'lane_to_serdes_map_fabric_lane193': 'rx389:tx384',
      'lane_to_serdes_map_fabric_lane194': 'rx386:tx389',
      'lane_to_serdes_map_fabric_lane195': 'rx387:tx390',
      'lane_to_serdes_map_fabric_lane448': 'rx384:tx391',
      'lane_to_serdes_map_fabric_lane449': 'rx385:tx388',
      'lane_to_serdes_map_fabric_lane450': 'rx390:tx385',
      'lane_to_serdes_map_fabric_lane451': 'rx391:tx386',
      'lane_to_serdes_map_fabric_lane196': 'rx396:tx395',
      'lane_to_serdes_map_fabric_lane197': 'rx397:tx392',
      'lane_to_serdes_map_fabric_lane198': 'rx394:tx397',
      'lane_to_serdes_map_fabric_lane199': 'rx395:tx398',
      'lane_to_serdes_map_fabric_lane452': 'rx392:tx399',
      'lane_to_serdes_map_fabric_lane453': 'rx393:tx396',
      'lane_to_serdes_map_fabric_lane454': 'rx398:tx393',
      'lane_to_serdes_map_fabric_lane455': 'rx399:tx394',
      'lane_to_serdes_map_fabric_lane200': 'rx404:tx400',
      'lane_to_serdes_map_fabric_lane201': 'rx405:tx401',
      'lane_to_serdes_map_fabric_lane202': 'rx402:tx406',
      'lane_to_serdes_map_fabric_lane203': 'rx403:tx407',
      'lane_to_serdes_map_fabric_lane456': 'rx400:tx404',
      'lane_to_serdes_map_fabric_lane457': 'rx401:tx405',
      'lane_to_serdes_map_fabric_lane458': 'rx406:tx402',
      'lane_to_serdes_map_fabric_lane459': 'rx407:tx403',
      'lane_to_serdes_map_fabric_lane204': 'rx412:tx408',
      'lane_to_serdes_map_fabric_lane205': 'rx413:tx409',
      'lane_to_serdes_map_fabric_lane206': 'rx410:tx414',
      'lane_to_serdes_map_fabric_lane207': 'rx411:tx415',
      'lane_to_serdes_map_fabric_lane460': 'rx408:tx412',
      'lane_to_serdes_map_fabric_lane461': 'rx409:tx413',
      'lane_to_serdes_map_fabric_lane462': 'rx414:tx410',
      'lane_to_serdes_map_fabric_lane463': 'rx415:tx411',
      'lane_to_serdes_map_fabric_lane208': 'rx420:tx419',
      'lane_to_serdes_map_fabric_lane209': 'rx421:tx416',
      'lane_to_serdes_map_fabric_lane210': 'rx418:tx421',
      'lane_to_serdes_map_fabric_lane211': 'rx419:tx422',
      'lane_to_serdes_map_fabric_lane464': 'rx416:tx423',
      'lane_to_serdes_map_fabric_lane465': 'rx417:tx420',
      'lane_to_serdes_map_fabric_lane466': 'rx422:tx417',
      'lane_to_serdes_map_fabric_lane467': 'rx423:tx418',
      'lane_to_serdes_map_fabric_lane212': 'rx428:tx427',
      'lane_to_serdes_map_fabric_lane213': 'rx429:tx424',
      'lane_to_serdes_map_fabric_lane214': 'rx426:tx429',
      'lane_to_serdes_map_fabric_lane215': 'rx427:tx430',
      'lane_to_serdes_map_fabric_lane468': 'rx424:tx431',
      'lane_to_serdes_map_fabric_lane469': 'rx425:tx428',
      'lane_to_serdes_map_fabric_lane470': 'rx430:tx425',
      'lane_to_serdes_map_fabric_lane471': 'rx431:tx426',
      'lane_to_serdes_map_fabric_lane216': 'rx436:tx432',
      'lane_to_serdes_map_fabric_lane217': 'rx437:tx433',
      'lane_to_serdes_map_fabric_lane218': 'rx434:tx438',
      'lane_to_serdes_map_fabric_lane219': 'rx435:tx439',
      'lane_to_serdes_map_fabric_lane472': 'rx432:tx436',
      'lane_to_serdes_map_fabric_lane473': 'rx433:tx437',
      'lane_to_serdes_map_fabric_lane474': 'rx438:tx434',
      'lane_to_serdes_map_fabric_lane475': 'rx439:tx435',
      'lane_to_serdes_map_fabric_lane220': 'rx444:tx440',
      'lane_to_serdes_map_fabric_lane221': 'rx445:tx441',
      'lane_to_serdes_map_fabric_lane222': 'rx442:tx446',
      'lane_to_serdes_map_fabric_lane223': 'rx443:tx447',
      'lane_to_serdes_map_fabric_lane476': 'rx440:tx444',
      'lane_to_serdes_map_fabric_lane477': 'rx441:tx445',
      'lane_to_serdes_map_fabric_lane478': 'rx446:tx442',
      'lane_to_serdes_map_fabric_lane479': 'rx447:tx443',
      'lane_to_serdes_map_fabric_lane224': 'rx452:tx451',
      'lane_to_serdes_map_fabric_lane225': 'rx453:tx448',
      'lane_to_serdes_map_fabric_lane226': 'rx450:tx453',
      'lane_to_serdes_map_fabric_lane227': 'rx451:tx454',
      'lane_to_serdes_map_fabric_lane480': 'rx448:tx455',
      'lane_to_serdes_map_fabric_lane481': 'rx449:tx452',
      'lane_to_serdes_map_fabric_lane482': 'rx454:tx449',
      'lane_to_serdes_map_fabric_lane483': 'rx455:tx450',
      'lane_to_serdes_map_fabric_lane228': 'rx460:tx459',
      'lane_to_serdes_map_fabric_lane229': 'rx461:tx456',
      'lane_to_serdes_map_fabric_lane230': 'rx458:tx461',
      'lane_to_serdes_map_fabric_lane231': 'rx459:tx462',
      'lane_to_serdes_map_fabric_lane484': 'rx456:tx463',
      'lane_to_serdes_map_fabric_lane485': 'rx457:tx460',
      'lane_to_serdes_map_fabric_lane486': 'rx462:tx457',
      'lane_to_serdes_map_fabric_lane487': 'rx463:tx458',
      'lane_to_serdes_map_fabric_lane232': 'rx468:tx464',
      'lane_to_serdes_map_fabric_lane233': 'rx469:tx465',
      'lane_to_serdes_map_fabric_lane234': 'rx466:tx470',
      'lane_to_serdes_map_fabric_lane235': 'rx467:tx471',
      'lane_to_serdes_map_fabric_lane488': 'rx464:tx468',
      'lane_to_serdes_map_fabric_lane489': 'rx465:tx469',
      'lane_to_serdes_map_fabric_lane490': 'rx470:tx466',
      'lane_to_serdes_map_fabric_lane491': 'rx471:tx467',
      'lane_to_serdes_map_fabric_lane236': 'rx472:tx472',
      'lane_to_serdes_map_fabric_lane237': 'rx473:tx473',
      'lane_to_serdes_map_fabric_lane238': 'rx478:tx478',
      'lane_to_serdes_map_fabric_lane239': 'rx479:tx479',
      'lane_to_serdes_map_fabric_lane492': 'rx476:tx476',
      'lane_to_serdes_map_fabric_lane493': 'rx477:tx477',
      'lane_to_serdes_map_fabric_lane494': 'rx474:tx474',
      'lane_to_serdes_map_fabric_lane495': 'rx475:tx475',
      'lane_to_serdes_map_fabric_lane240': 'rx484:tx485',
      'lane_to_serdes_map_fabric_lane241': 'rx485:tx484',
      'lane_to_serdes_map_fabric_lane242': 'rx482:tx483',
      'lane_to_serdes_map_fabric_lane243': 'rx483:tx482',
      'lane_to_serdes_map_fabric_lane496': 'rx480:tx481',
      'lane_to_serdes_map_fabric_lane497': 'rx481:tx480',
      'lane_to_serdes_map_fabric_lane498': 'rx486:tx487',
      'lane_to_serdes_map_fabric_lane499': 'rx487:tx486',
      'lane_to_serdes_map_fabric_lane244': 'rx488:tx489',
      'lane_to_serdes_map_fabric_lane245': 'rx489:tx488',
      'lane_to_serdes_map_fabric_lane246': 'rx494:tx495',
      'lane_to_serdes_map_fabric_lane247': 'rx495:tx494',
      'lane_to_serdes_map_fabric_lane500': 'rx492:tx493',
      'lane_to_serdes_map_fabric_lane501': 'rx493:tx492',
      'lane_to_serdes_map_fabric_lane502': 'rx490:tx491',
      'lane_to_serdes_map_fabric_lane503': 'rx491:tx490',
      'lane_to_serdes_map_fabric_lane248': 'rx500:tx500',
      'lane_to_serdes_map_fabric_lane249': 'rx501:tx501',
      'lane_to_serdes_map_fabric_lane250': 'rx498:tx498',
      'lane_to_serdes_map_fabric_lane251': 'rx499:tx499',
      'lane_to_serdes_map_fabric_lane504': 'rx496:tx496',
      'lane_to_serdes_map_fabric_lane505': 'rx497:tx497',
      'lane_to_serdes_map_fabric_lane506': 'rx502:tx502',
      'lane_to_serdes_map_fabric_lane507': 'rx503:tx503',
      'lane_to_serdes_map_fabric_lane252': 'rx504:tx504',
      'lane_to_serdes_map_fabric_lane253': 'rx505:tx505',
      'lane_to_serdes_map_fabric_lane254': 'rx510:tx510',
      'lane_to_serdes_map_fabric_lane255': 'rx511:tx511',
      'lane_to_serdes_map_fabric_lane508': 'rx508:tx508',
      'lane_to_serdes_map_fabric_lane509': 'rx509:tx509',
      'lane_to_serdes_map_fabric_lane510': 'rx506:tx506',
      'lane_to_serdes_map_fabric_lane511': 'rx507:tx507',
   },
   { # fe1
      'lane_to_serdes_map_fabric_lane0': 'rx0:tx1',
      'lane_to_serdes_map_fabric_lane1': 'rx1:tx0',
      'lane_to_serdes_map_fabric_lane2': 'rx6:tx7',
      'lane_to_serdes_map_fabric_lane3': 'rx7:tx6',
      'lane_to_serdes_map_fabric_lane256': 'rx4:tx5',
      'lane_to_serdes_map_fabric_lane257': 'rx5:tx4',
      'lane_to_serdes_map_fabric_lane258': 'rx2:tx3',
      'lane_to_serdes_map_fabric_lane259': 'rx3:tx2',
      'lane_to_serdes_map_fabric_lane4': 'rx12:tx13',
      'lane_to_serdes_map_fabric_lane5': 'rx13:tx12',
      'lane_to_serdes_map_fabric_lane6': 'rx10:tx11',
      'lane_to_serdes_map_fabric_lane7': 'rx11:tx10',
      'lane_to_serdes_map_fabric_lane260': 'rx8:tx9',
      'lane_to_serdes_map_fabric_lane261': 'rx9:tx8',
      'lane_to_serdes_map_fabric_lane262': 'rx14:tx15',
      'lane_to_serdes_map_fabric_lane263': 'rx15:tx14',
      'lane_to_serdes_map_fabric_lane8': 'rx16:tx16',
      'lane_to_serdes_map_fabric_lane9': 'rx17:tx17',
      'lane_to_serdes_map_fabric_lane10': 'rx22:tx22',
      'lane_to_serdes_map_fabric_lane11': 'rx23:tx23',
      'lane_to_serdes_map_fabric_lane264': 'rx20:tx20',
      'lane_to_serdes_map_fabric_lane265': 'rx21:tx21',
      'lane_to_serdes_map_fabric_lane266': 'rx18:tx18',
      'lane_to_serdes_map_fabric_lane267': 'rx19:tx19',
      'lane_to_serdes_map_fabric_lane12': 'rx28:tx28',
      'lane_to_serdes_map_fabric_lane13': 'rx29:tx29',
      'lane_to_serdes_map_fabric_lane14': 'rx26:tx26',
      'lane_to_serdes_map_fabric_lane15': 'rx27:tx27',
      'lane_to_serdes_map_fabric_lane268': 'rx24:tx24',
      'lane_to_serdes_map_fabric_lane269': 'rx25:tx25',
      'lane_to_serdes_map_fabric_lane270': 'rx30:tx30',
      'lane_to_serdes_map_fabric_lane271': 'rx31:tx31',
      'lane_to_serdes_map_fabric_lane16': 'rx32:tx33',
      'lane_to_serdes_map_fabric_lane17': 'rx33:tx34',
      'lane_to_serdes_map_fabric_lane18': 'rx38:tx39',
      'lane_to_serdes_map_fabric_lane19': 'rx39:tx36',
      'lane_to_serdes_map_fabric_lane272': 'rx36:tx37',
      'lane_to_serdes_map_fabric_lane273': 'rx37:tx38',
      'lane_to_serdes_map_fabric_lane274': 'rx34:tx35',
      'lane_to_serdes_map_fabric_lane275': 'rx35:tx32',
      'lane_to_serdes_map_fabric_lane20': 'rx44:tx41',
      'lane_to_serdes_map_fabric_lane21': 'rx45:tx42',
      'lane_to_serdes_map_fabric_lane22': 'rx42:tx47',
      'lane_to_serdes_map_fabric_lane23': 'rx43:tx44',
      'lane_to_serdes_map_fabric_lane276': 'rx40:tx45',
      'lane_to_serdes_map_fabric_lane277': 'rx41:tx46',
      'lane_to_serdes_map_fabric_lane278': 'rx46:tx43',
      'lane_to_serdes_map_fabric_lane279': 'rx47:tx40',
      'lane_to_serdes_map_fabric_lane24': 'rx52:tx48',
      'lane_to_serdes_map_fabric_lane25': 'rx53:tx49',
      'lane_to_serdes_map_fabric_lane26': 'rx50:tx54',
      'lane_to_serdes_map_fabric_lane27': 'rx51:tx55',
      'lane_to_serdes_map_fabric_lane280': 'rx48:tx52',
      'lane_to_serdes_map_fabric_lane281': 'rx49:tx53',
      'lane_to_serdes_map_fabric_lane282': 'rx54:tx50',
      'lane_to_serdes_map_fabric_lane283': 'rx55:tx51',
      'lane_to_serdes_map_fabric_lane28': 'rx60:tx56',
      'lane_to_serdes_map_fabric_lane29': 'rx61:tx57',
      'lane_to_serdes_map_fabric_lane30': 'rx58:tx62',
      'lane_to_serdes_map_fabric_lane31': 'rx59:tx63',
      'lane_to_serdes_map_fabric_lane284': 'rx56:tx60',
      'lane_to_serdes_map_fabric_lane285': 'rx57:tx61',
      'lane_to_serdes_map_fabric_lane286': 'rx62:tx58',
      'lane_to_serdes_map_fabric_lane287': 'rx63:tx59',
      'lane_to_serdes_map_fabric_lane32': 'rx68:tx65',
      'lane_to_serdes_map_fabric_lane33': 'rx69:tx66',
      'lane_to_serdes_map_fabric_lane34': 'rx66:tx71',
      'lane_to_serdes_map_fabric_lane35': 'rx67:tx68',
      'lane_to_serdes_map_fabric_lane288': 'rx64:tx69',
      'lane_to_serdes_map_fabric_lane289': 'rx65:tx70',
      'lane_to_serdes_map_fabric_lane290': 'rx70:tx67',
      'lane_to_serdes_map_fabric_lane291': 'rx71:tx64',
      'lane_to_serdes_map_fabric_lane36': 'rx76:tx73',
      'lane_to_serdes_map_fabric_lane37': 'rx77:tx74',
      'lane_to_serdes_map_fabric_lane38': 'rx74:tx79',
      'lane_to_serdes_map_fabric_lane39': 'rx75:tx76',
      'lane_to_serdes_map_fabric_lane292': 'rx72:tx77',
      'lane_to_serdes_map_fabric_lane293': 'rx73:tx78',
      'lane_to_serdes_map_fabric_lane294': 'rx78:tx75',
      'lane_to_serdes_map_fabric_lane295': 'rx79:tx72',
      'lane_to_serdes_map_fabric_lane40': 'rx84:tx80',
      'lane_to_serdes_map_fabric_lane41': 'rx85:tx81',
      'lane_to_serdes_map_fabric_lane42': 'rx82:tx86',
      'lane_to_serdes_map_fabric_lane43': 'rx83:tx87',
      'lane_to_serdes_map_fabric_lane296': 'rx80:tx84',
      'lane_to_serdes_map_fabric_lane297': 'rx81:tx85',
      'lane_to_serdes_map_fabric_lane298': 'rx86:tx82',
      'lane_to_serdes_map_fabric_lane299': 'rx87:tx83',
      'lane_to_serdes_map_fabric_lane44': 'rx92:tx88',
      'lane_to_serdes_map_fabric_lane45': 'rx93:tx89',
      'lane_to_serdes_map_fabric_lane46': 'rx90:tx94',
      'lane_to_serdes_map_fabric_lane47': 'rx91:tx95',
      'lane_to_serdes_map_fabric_lane300': 'rx88:tx92',
      'lane_to_serdes_map_fabric_lane301': 'rx89:tx93',
      'lane_to_serdes_map_fabric_lane302': 'rx94:tx90',
      'lane_to_serdes_map_fabric_lane303': 'rx95:tx91',
      'lane_to_serdes_map_fabric_lane48': 'rx100:tx97',
      'lane_to_serdes_map_fabric_lane49': 'rx101:tx98',
      'lane_to_serdes_map_fabric_lane50': 'rx98:tx103',
      'lane_to_serdes_map_fabric_lane51': 'rx99:tx100',
      'lane_to_serdes_map_fabric_lane304': 'rx96:tx101',
      'lane_to_serdes_map_fabric_lane305': 'rx97:tx102',
      'lane_to_serdes_map_fabric_lane306': 'rx102:tx99',
      'lane_to_serdes_map_fabric_lane307': 'rx103:tx96',
      'lane_to_serdes_map_fabric_lane52': 'rx108:tx105',
      'lane_to_serdes_map_fabric_lane53': 'rx109:tx106',
      'lane_to_serdes_map_fabric_lane54': 'rx106:tx111',
      'lane_to_serdes_map_fabric_lane55': 'rx107:tx108',
      'lane_to_serdes_map_fabric_lane308': 'rx104:tx109',
      'lane_to_serdes_map_fabric_lane309': 'rx105:tx110',
      'lane_to_serdes_map_fabric_lane310': 'rx110:tx107',
      'lane_to_serdes_map_fabric_lane311': 'rx111:tx104',
      'lane_to_serdes_map_fabric_lane56': 'rx116:tx112',
      'lane_to_serdes_map_fabric_lane57': 'rx117:tx113',
      'lane_to_serdes_map_fabric_lane58': 'rx114:tx118',
      'lane_to_serdes_map_fabric_lane59': 'rx115:tx119',
      'lane_to_serdes_map_fabric_lane312': 'rx112:tx116',
      'lane_to_serdes_map_fabric_lane313': 'rx113:tx117',
      'lane_to_serdes_map_fabric_lane314': 'rx118:tx114',
      'lane_to_serdes_map_fabric_lane315': 'rx119:tx115',
      'lane_to_serdes_map_fabric_lane60': 'rx124:tx120',
      'lane_to_serdes_map_fabric_lane61': 'rx125:tx121',
      'lane_to_serdes_map_fabric_lane62': 'rx122:tx126',
      'lane_to_serdes_map_fabric_lane63': 'rx123:tx127',
      'lane_to_serdes_map_fabric_lane316': 'rx120:tx124',
      'lane_to_serdes_map_fabric_lane317': 'rx121:tx125',
      'lane_to_serdes_map_fabric_lane318': 'rx126:tx122',
      'lane_to_serdes_map_fabric_lane319': 'rx127:tx123',
      'lane_to_serdes_map_fabric_lane64': 'rx128:tx133',
      'lane_to_serdes_map_fabric_lane65': 'rx129:tx134',
      'lane_to_serdes_map_fabric_lane66': 'rx134:tx131',
      'lane_to_serdes_map_fabric_lane67': 'rx135:tx128',
      'lane_to_serdes_map_fabric_lane320': 'rx132:tx129',
      'lane_to_serdes_map_fabric_lane321': 'rx133:tx130',
      'lane_to_serdes_map_fabric_lane322': 'rx130:tx135',
      'lane_to_serdes_map_fabric_lane323': 'rx131:tx132',
      'lane_to_serdes_map_fabric_lane68': 'rx136:tx141',
      'lane_to_serdes_map_fabric_lane69': 'rx137:tx142',
      'lane_to_serdes_map_fabric_lane70': 'rx142:tx139',
      'lane_to_serdes_map_fabric_lane71': 'rx143:tx136',
      'lane_to_serdes_map_fabric_lane324': 'rx140:tx137',
      'lane_to_serdes_map_fabric_lane325': 'rx141:tx138',
      'lane_to_serdes_map_fabric_lane326': 'rx138:tx143',
      'lane_to_serdes_map_fabric_lane327': 'rx139:tx140',
      'lane_to_serdes_map_fabric_lane72': 'rx144:tx148',
      'lane_to_serdes_map_fabric_lane73': 'rx145:tx149',
      'lane_to_serdes_map_fabric_lane74': 'rx150:tx146',
      'lane_to_serdes_map_fabric_lane75': 'rx151:tx147',
      'lane_to_serdes_map_fabric_lane328': 'rx148:tx144',
      'lane_to_serdes_map_fabric_lane329': 'rx149:tx145',
      'lane_to_serdes_map_fabric_lane330': 'rx146:tx150',
      'lane_to_serdes_map_fabric_lane331': 'rx147:tx151',
      'lane_to_serdes_map_fabric_lane76': 'rx152:tx156',
      'lane_to_serdes_map_fabric_lane77': 'rx153:tx157',
      'lane_to_serdes_map_fabric_lane78': 'rx158:tx154',
      'lane_to_serdes_map_fabric_lane79': 'rx159:tx155',
      'lane_to_serdes_map_fabric_lane332': 'rx156:tx152',
      'lane_to_serdes_map_fabric_lane333': 'rx157:tx153',
      'lane_to_serdes_map_fabric_lane334': 'rx154:tx158',
      'lane_to_serdes_map_fabric_lane335': 'rx155:tx159',
      'lane_to_serdes_map_fabric_lane80': 'rx160:tx165',
      'lane_to_serdes_map_fabric_lane81': 'rx161:tx166',
      'lane_to_serdes_map_fabric_lane82': 'rx166:tx163',
      'lane_to_serdes_map_fabric_lane83': 'rx167:tx160',
      'lane_to_serdes_map_fabric_lane336': 'rx164:tx161',
      'lane_to_serdes_map_fabric_lane337': 'rx165:tx162',
      'lane_to_serdes_map_fabric_lane338': 'rx162:tx167',
      'lane_to_serdes_map_fabric_lane339': 'rx163:tx164',
      'lane_to_serdes_map_fabric_lane84': 'rx168:tx173',
      'lane_to_serdes_map_fabric_lane85': 'rx169:tx174',
      'lane_to_serdes_map_fabric_lane86': 'rx174:tx171',
      'lane_to_serdes_map_fabric_lane87': 'rx175:tx168',
      'lane_to_serdes_map_fabric_lane340': 'rx172:tx169',
      'lane_to_serdes_map_fabric_lane341': 'rx173:tx170',
      'lane_to_serdes_map_fabric_lane342': 'rx170:tx175',
      'lane_to_serdes_map_fabric_lane343': 'rx171:tx172',
      'lane_to_serdes_map_fabric_lane88': 'rx176:tx180',
      'lane_to_serdes_map_fabric_lane89': 'rx177:tx181',
      'lane_to_serdes_map_fabric_lane90': 'rx182:tx178',
      'lane_to_serdes_map_fabric_lane91': 'rx183:tx179',
      'lane_to_serdes_map_fabric_lane344': 'rx180:tx176',
      'lane_to_serdes_map_fabric_lane345': 'rx181:tx177',
      'lane_to_serdes_map_fabric_lane346': 'rx178:tx182',
      'lane_to_serdes_map_fabric_lane347': 'rx179:tx183',
      'lane_to_serdes_map_fabric_lane92': 'rx184:tx188',
      'lane_to_serdes_map_fabric_lane93': 'rx185:tx189',
      'lane_to_serdes_map_fabric_lane94': 'rx190:tx186',
      'lane_to_serdes_map_fabric_lane95': 'rx191:tx187',
      'lane_to_serdes_map_fabric_lane348': 'rx188:tx184',
      'lane_to_serdes_map_fabric_lane349': 'rx189:tx185',
      'lane_to_serdes_map_fabric_lane350': 'rx186:tx190',
      'lane_to_serdes_map_fabric_lane351': 'rx187:tx191',
      'lane_to_serdes_map_fabric_lane96': 'rx192:tx197',
      'lane_to_serdes_map_fabric_lane97': 'rx193:tx198',
      'lane_to_serdes_map_fabric_lane98': 'rx198:tx195',
      'lane_to_serdes_map_fabric_lane99': 'rx199:tx192',
      'lane_to_serdes_map_fabric_lane352': 'rx196:tx193',
      'lane_to_serdes_map_fabric_lane353': 'rx197:tx194',
      'lane_to_serdes_map_fabric_lane354': 'rx194:tx199',
      'lane_to_serdes_map_fabric_lane355': 'rx195:tx196',
      'lane_to_serdes_map_fabric_lane100': 'rx200:tx205',
      'lane_to_serdes_map_fabric_lane101': 'rx201:tx206',
      'lane_to_serdes_map_fabric_lane102': 'rx206:tx203',
      'lane_to_serdes_map_fabric_lane103': 'rx207:tx200',
      'lane_to_serdes_map_fabric_lane356': 'rx204:tx201',
      'lane_to_serdes_map_fabric_lane357': 'rx205:tx202',
      'lane_to_serdes_map_fabric_lane358': 'rx202:tx207',
      'lane_to_serdes_map_fabric_lane359': 'rx203:tx204',
      'lane_to_serdes_map_fabric_lane104': 'rx208:tx212',
      'lane_to_serdes_map_fabric_lane105': 'rx209:tx213',
      'lane_to_serdes_map_fabric_lane106': 'rx214:tx210',
      'lane_to_serdes_map_fabric_lane107': 'rx215:tx211',
      'lane_to_serdes_map_fabric_lane360': 'rx212:tx208',
      'lane_to_serdes_map_fabric_lane361': 'rx213:tx209',
      'lane_to_serdes_map_fabric_lane362': 'rx210:tx214',
      'lane_to_serdes_map_fabric_lane363': 'rx211:tx215',
      'lane_to_serdes_map_fabric_lane108': 'rx216:tx220',
      'lane_to_serdes_map_fabric_lane109': 'rx217:tx221',
      'lane_to_serdes_map_fabric_lane110': 'rx222:tx218',
      'lane_to_serdes_map_fabric_lane111': 'rx223:tx219',
      'lane_to_serdes_map_fabric_lane364': 'rx220:tx216',
      'lane_to_serdes_map_fabric_lane365': 'rx221:tx217',
      'lane_to_serdes_map_fabric_lane366': 'rx218:tx222',
      'lane_to_serdes_map_fabric_lane367': 'rx219:tx223',
      'lane_to_serdes_map_fabric_lane112': 'rx228:tx229',
      'lane_to_serdes_map_fabric_lane113': 'rx229:tx228',
      'lane_to_serdes_map_fabric_lane114': 'rx226:tx227',
      'lane_to_serdes_map_fabric_lane115': 'rx227:tx226',
      'lane_to_serdes_map_fabric_lane368': 'rx224:tx225',
      'lane_to_serdes_map_fabric_lane369': 'rx225:tx224',
      'lane_to_serdes_map_fabric_lane370': 'rx230:tx231',
      'lane_to_serdes_map_fabric_lane371': 'rx231:tx230',
      'lane_to_serdes_map_fabric_lane116': 'rx232:tx233',
      'lane_to_serdes_map_fabric_lane117': 'rx233:tx232',
      'lane_to_serdes_map_fabric_lane118': 'rx238:tx239',
      'lane_to_serdes_map_fabric_lane119': 'rx239:tx238',
      'lane_to_serdes_map_fabric_lane372': 'rx236:tx237',
      'lane_to_serdes_map_fabric_lane373': 'rx237:tx236',
      'lane_to_serdes_map_fabric_lane374': 'rx234:tx235',
      'lane_to_serdes_map_fabric_lane375': 'rx235:tx234',
      'lane_to_serdes_map_fabric_lane120': 'rx244:tx244',
      'lane_to_serdes_map_fabric_lane121': 'rx245:tx245',
      'lane_to_serdes_map_fabric_lane122': 'rx242:tx242',
      'lane_to_serdes_map_fabric_lane123': 'rx243:tx243',
      'lane_to_serdes_map_fabric_lane376': 'rx240:tx240',
      'lane_to_serdes_map_fabric_lane377': 'rx241:tx241',
      'lane_to_serdes_map_fabric_lane378': 'rx246:tx246',
      'lane_to_serdes_map_fabric_lane379': 'rx247:tx247',
      'lane_to_serdes_map_fabric_lane124': 'rx248:tx248',
      'lane_to_serdes_map_fabric_lane125': 'rx249:tx249',
      'lane_to_serdes_map_fabric_lane126': 'rx254:tx254',
      'lane_to_serdes_map_fabric_lane127': 'rx255:tx255',
      'lane_to_serdes_map_fabric_lane380': 'rx252:tx252',
      'lane_to_serdes_map_fabric_lane381': 'rx253:tx253',
      'lane_to_serdes_map_fabric_lane382': 'rx250:tx250',
      'lane_to_serdes_map_fabric_lane383': 'rx251:tx251',
      'lane_to_serdes_map_fabric_lane128': 'rx256:tx257',
      'lane_to_serdes_map_fabric_lane129': 'rx257:tx256',
      'lane_to_serdes_map_fabric_lane130': 'rx262:tx263',
      'lane_to_serdes_map_fabric_lane131': 'rx263:tx262',
      'lane_to_serdes_map_fabric_lane384': 'rx260:tx261',
      'lane_to_serdes_map_fabric_lane385': 'rx261:tx260',
      'lane_to_serdes_map_fabric_lane386': 'rx258:tx259',
      'lane_to_serdes_map_fabric_lane387': 'rx259:tx258',
      'lane_to_serdes_map_fabric_lane132': 'rx268:tx269',
      'lane_to_serdes_map_fabric_lane133': 'rx269:tx268',
      'lane_to_serdes_map_fabric_lane134': 'rx266:tx267',
      'lane_to_serdes_map_fabric_lane135': 'rx267:tx266',
      'lane_to_serdes_map_fabric_lane388': 'rx264:tx265',
      'lane_to_serdes_map_fabric_lane389': 'rx265:tx264',
      'lane_to_serdes_map_fabric_lane390': 'rx270:tx271',
      'lane_to_serdes_map_fabric_lane391': 'rx271:tx270',
      'lane_to_serdes_map_fabric_lane136': 'rx272:tx272',
      'lane_to_serdes_map_fabric_lane137': 'rx273:tx273',
      'lane_to_serdes_map_fabric_lane138': 'rx278:tx278',
      'lane_to_serdes_map_fabric_lane139': 'rx279:tx279',
      'lane_to_serdes_map_fabric_lane392': 'rx276:tx276',
      'lane_to_serdes_map_fabric_lane393': 'rx277:tx277',
      'lane_to_serdes_map_fabric_lane394': 'rx274:tx274',
      'lane_to_serdes_map_fabric_lane395': 'rx275:tx275',
      'lane_to_serdes_map_fabric_lane140': 'rx284:tx284',
      'lane_to_serdes_map_fabric_lane141': 'rx285:tx285',
      'lane_to_serdes_map_fabric_lane142': 'rx282:tx282',
      'lane_to_serdes_map_fabric_lane143': 'rx283:tx283',
      'lane_to_serdes_map_fabric_lane396': 'rx280:tx280',
      'lane_to_serdes_map_fabric_lane397': 'rx281:tx281',
      'lane_to_serdes_map_fabric_lane398': 'rx286:tx286',
      'lane_to_serdes_map_fabric_lane399': 'rx287:tx287',
      'lane_to_serdes_map_fabric_lane144': 'rx292:tx289',
      'lane_to_serdes_map_fabric_lane145': 'rx293:tx290',
      'lane_to_serdes_map_fabric_lane146': 'rx290:tx295',
      'lane_to_serdes_map_fabric_lane147': 'rx291:tx292',
      'lane_to_serdes_map_fabric_lane400': 'rx288:tx293',
      'lane_to_serdes_map_fabric_lane401': 'rx289:tx294',
      'lane_to_serdes_map_fabric_lane402': 'rx294:tx291',
      'lane_to_serdes_map_fabric_lane403': 'rx295:tx288',
      'lane_to_serdes_map_fabric_lane148': 'rx300:tx297',
      'lane_to_serdes_map_fabric_lane149': 'rx301:tx298',
      'lane_to_serdes_map_fabric_lane150': 'rx298:tx303',
      'lane_to_serdes_map_fabric_lane151': 'rx299:tx300',
      'lane_to_serdes_map_fabric_lane404': 'rx296:tx301',
      'lane_to_serdes_map_fabric_lane405': 'rx297:tx302',
      'lane_to_serdes_map_fabric_lane406': 'rx302:tx299',
      'lane_to_serdes_map_fabric_lane407': 'rx303:tx296',
      'lane_to_serdes_map_fabric_lane152': 'rx308:tx304',
      'lane_to_serdes_map_fabric_lane153': 'rx309:tx305',
      'lane_to_serdes_map_fabric_lane154': 'rx306:tx310',
      'lane_to_serdes_map_fabric_lane155': 'rx307:tx311',
      'lane_to_serdes_map_fabric_lane408': 'rx304:tx308',
      'lane_to_serdes_map_fabric_lane409': 'rx305:tx309',
      'lane_to_serdes_map_fabric_lane410': 'rx310:tx306',
      'lane_to_serdes_map_fabric_lane411': 'rx311:tx307',
      'lane_to_serdes_map_fabric_lane156': 'rx316:tx312',
      'lane_to_serdes_map_fabric_lane157': 'rx317:tx313',
      'lane_to_serdes_map_fabric_lane158': 'rx314:tx318',
      'lane_to_serdes_map_fabric_lane159': 'rx315:tx319',
      'lane_to_serdes_map_fabric_lane412': 'rx312:tx316',
      'lane_to_serdes_map_fabric_lane413': 'rx313:tx317',
      'lane_to_serdes_map_fabric_lane414': 'rx318:tx314',
      'lane_to_serdes_map_fabric_lane415': 'rx319:tx315',
      'lane_to_serdes_map_fabric_lane160': 'rx324:tx321',
      'lane_to_serdes_map_fabric_lane161': 'rx325:tx322',
      'lane_to_serdes_map_fabric_lane162': 'rx322:tx327',
      'lane_to_serdes_map_fabric_lane163': 'rx323:tx324',
      'lane_to_serdes_map_fabric_lane416': 'rx320:tx325',
      'lane_to_serdes_map_fabric_lane417': 'rx321:tx326',
      'lane_to_serdes_map_fabric_lane418': 'rx326:tx323',
      'lane_to_serdes_map_fabric_lane419': 'rx327:tx320',
      'lane_to_serdes_map_fabric_lane164': 'rx332:tx329',
      'lane_to_serdes_map_fabric_lane165': 'rx333:tx330',
      'lane_to_serdes_map_fabric_lane166': 'rx330:tx335',
      'lane_to_serdes_map_fabric_lane167': 'rx331:tx332',
      'lane_to_serdes_map_fabric_lane420': 'rx328:tx333',
      'lane_to_serdes_map_fabric_lane421': 'rx329:tx334',
      'lane_to_serdes_map_fabric_lane422': 'rx334:tx331',
      'lane_to_serdes_map_fabric_lane423': 'rx335:tx328',
      'lane_to_serdes_map_fabric_lane168': 'rx340:tx336',
      'lane_to_serdes_map_fabric_lane169': 'rx341:tx337',
      'lane_to_serdes_map_fabric_lane170': 'rx338:tx342',
      'lane_to_serdes_map_fabric_lane171': 'rx339:tx343',
      'lane_to_serdes_map_fabric_lane424': 'rx336:tx340',
      'lane_to_serdes_map_fabric_lane425': 'rx337:tx341',
      'lane_to_serdes_map_fabric_lane426': 'rx342:tx338',
      'lane_to_serdes_map_fabric_lane427': 'rx343:tx339',
      'lane_to_serdes_map_fabric_lane172': 'rx348:tx344',
      'lane_to_serdes_map_fabric_lane173': 'rx349:tx345',
      'lane_to_serdes_map_fabric_lane174': 'rx346:tx350',
      'lane_to_serdes_map_fabric_lane175': 'rx347:tx351',
      'lane_to_serdes_map_fabric_lane428': 'rx344:tx348',
      'lane_to_serdes_map_fabric_lane429': 'rx345:tx349',
      'lane_to_serdes_map_fabric_lane430': 'rx350:tx346',
      'lane_to_serdes_map_fabric_lane431': 'rx351:tx347',
      'lane_to_serdes_map_fabric_lane176': 'rx356:tx353',
      'lane_to_serdes_map_fabric_lane177': 'rx357:tx354',
      'lane_to_serdes_map_fabric_lane178': 'rx354:tx359',
      'lane_to_serdes_map_fabric_lane179': 'rx355:tx356',
      'lane_to_serdes_map_fabric_lane432': 'rx352:tx357',
      'lane_to_serdes_map_fabric_lane433': 'rx353:tx358',
      'lane_to_serdes_map_fabric_lane434': 'rx358:tx355',
      'lane_to_serdes_map_fabric_lane435': 'rx359:tx352',
      'lane_to_serdes_map_fabric_lane180': 'rx364:tx361',
      'lane_to_serdes_map_fabric_lane181': 'rx365:tx362',
      'lane_to_serdes_map_fabric_lane182': 'rx362:tx367',
      'lane_to_serdes_map_fabric_lane183': 'rx363:tx364',
      'lane_to_serdes_map_fabric_lane436': 'rx360:tx365',
      'lane_to_serdes_map_fabric_lane437': 'rx361:tx366',
      'lane_to_serdes_map_fabric_lane438': 'rx366:tx363',
      'lane_to_serdes_map_fabric_lane439': 'rx367:tx360',
      'lane_to_serdes_map_fabric_lane184': 'rx372:tx368',
      'lane_to_serdes_map_fabric_lane185': 'rx373:tx369',
      'lane_to_serdes_map_fabric_lane186': 'rx370:tx374',
      'lane_to_serdes_map_fabric_lane187': 'rx371:tx375',
      'lane_to_serdes_map_fabric_lane440': 'rx368:tx372',
      'lane_to_serdes_map_fabric_lane441': 'rx369:tx373',
      'lane_to_serdes_map_fabric_lane442': 'rx374:tx370',
      'lane_to_serdes_map_fabric_lane443': 'rx375:tx371',
      'lane_to_serdes_map_fabric_lane188': 'rx380:tx376',
      'lane_to_serdes_map_fabric_lane189': 'rx381:tx377',
      'lane_to_serdes_map_fabric_lane190': 'rx378:tx382',
      'lane_to_serdes_map_fabric_lane191': 'rx379:tx383',
      'lane_to_serdes_map_fabric_lane444': 'rx376:tx380',
      'lane_to_serdes_map_fabric_lane445': 'rx377:tx381',
      'lane_to_serdes_map_fabric_lane446': 'rx382:tx378',
      'lane_to_serdes_map_fabric_lane447': 'rx383:tx379',
      'lane_to_serdes_map_fabric_lane192': 'rx384:tx389',
      'lane_to_serdes_map_fabric_lane193': 'rx385:tx390',
      'lane_to_serdes_map_fabric_lane194': 'rx390:tx387',
      'lane_to_serdes_map_fabric_lane195': 'rx391:tx384',
      'lane_to_serdes_map_fabric_lane448': 'rx388:tx385',
      'lane_to_serdes_map_fabric_lane449': 'rx389:tx386',
      'lane_to_serdes_map_fabric_lane450': 'rx386:tx391',
      'lane_to_serdes_map_fabric_lane451': 'rx387:tx388',
      'lane_to_serdes_map_fabric_lane196': 'rx392:tx397',
      'lane_to_serdes_map_fabric_lane197': 'rx393:tx398',
      'lane_to_serdes_map_fabric_lane198': 'rx398:tx395',
      'lane_to_serdes_map_fabric_lane199': 'rx399:tx392',
      'lane_to_serdes_map_fabric_lane452': 'rx396:tx393',
      'lane_to_serdes_map_fabric_lane453': 'rx397:tx394',
      'lane_to_serdes_map_fabric_lane454': 'rx394:tx399',
      'lane_to_serdes_map_fabric_lane455': 'rx395:tx396',
      'lane_to_serdes_map_fabric_lane200': 'rx400:tx404',
      'lane_to_serdes_map_fabric_lane201': 'rx401:tx405',
      'lane_to_serdes_map_fabric_lane202': 'rx406:tx402',
      'lane_to_serdes_map_fabric_lane203': 'rx407:tx403',
      'lane_to_serdes_map_fabric_lane456': 'rx404:tx400',
      'lane_to_serdes_map_fabric_lane457': 'rx405:tx401',
      'lane_to_serdes_map_fabric_lane458': 'rx402:tx406',
      'lane_to_serdes_map_fabric_lane459': 'rx403:tx407',
      'lane_to_serdes_map_fabric_lane204': 'rx408:tx412',
      'lane_to_serdes_map_fabric_lane205': 'rx409:tx413',
      'lane_to_serdes_map_fabric_lane206': 'rx414:tx410',
      'lane_to_serdes_map_fabric_lane207': 'rx415:tx411',
      'lane_to_serdes_map_fabric_lane460': 'rx412:tx408',
      'lane_to_serdes_map_fabric_lane461': 'rx413:tx409',
      'lane_to_serdes_map_fabric_lane462': 'rx410:tx414',
      'lane_to_serdes_map_fabric_lane463': 'rx411:tx415',
      'lane_to_serdes_map_fabric_lane208': 'rx416:tx421',
      'lane_to_serdes_map_fabric_lane209': 'rx417:tx422',
      'lane_to_serdes_map_fabric_lane210': 'rx422:tx419',
      'lane_to_serdes_map_fabric_lane211': 'rx423:tx416',
      'lane_to_serdes_map_fabric_lane464': 'rx420:tx417',
      'lane_to_serdes_map_fabric_lane465': 'rx421:tx418',
      'lane_to_serdes_map_fabric_lane466': 'rx418:tx423',
      'lane_to_serdes_map_fabric_lane467': 'rx419:tx420',
      'lane_to_serdes_map_fabric_lane212': 'rx424:tx429',
      'lane_to_serdes_map_fabric_lane213': 'rx425:tx430',
      'lane_to_serdes_map_fabric_lane214': 'rx430:tx427',
      'lane_to_serdes_map_fabric_lane215': 'rx431:tx424',
      'lane_to_serdes_map_fabric_lane468': 'rx428:tx425',
      'lane_to_serdes_map_fabric_lane469': 'rx429:tx426',
      'lane_to_serdes_map_fabric_lane470': 'rx426:tx431',
      'lane_to_serdes_map_fabric_lane471': 'rx427:tx428',
      'lane_to_serdes_map_fabric_lane216': 'rx432:tx436',
      'lane_to_serdes_map_fabric_lane217': 'rx433:tx437',
      'lane_to_serdes_map_fabric_lane218': 'rx438:tx434',
      'lane_to_serdes_map_fabric_lane219': 'rx439:tx435',
      'lane_to_serdes_map_fabric_lane472': 'rx436:tx432',
      'lane_to_serdes_map_fabric_lane473': 'rx437:tx433',
      'lane_to_serdes_map_fabric_lane474': 'rx434:tx438',
      'lane_to_serdes_map_fabric_lane475': 'rx435:tx439',
      'lane_to_serdes_map_fabric_lane220': 'rx440:tx444',
      'lane_to_serdes_map_fabric_lane221': 'rx441:tx445',
      'lane_to_serdes_map_fabric_lane222': 'rx446:tx442',
      'lane_to_serdes_map_fabric_lane223': 'rx447:tx443',
      'lane_to_serdes_map_fabric_lane476': 'rx444:tx440',
      'lane_to_serdes_map_fabric_lane477': 'rx445:tx441',
      'lane_to_serdes_map_fabric_lane478': 'rx442:tx446',
      'lane_to_serdes_map_fabric_lane479': 'rx443:tx447',
      'lane_to_serdes_map_fabric_lane224': 'rx448:tx453',
      'lane_to_serdes_map_fabric_lane225': 'rx449:tx454',
      'lane_to_serdes_map_fabric_lane226': 'rx454:tx451',
      'lane_to_serdes_map_fabric_lane227': 'rx455:tx448',
      'lane_to_serdes_map_fabric_lane480': 'rx452:tx449',
      'lane_to_serdes_map_fabric_lane481': 'rx453:tx450',
      'lane_to_serdes_map_fabric_lane482': 'rx450:tx455',
      'lane_to_serdes_map_fabric_lane483': 'rx451:tx452',
      'lane_to_serdes_map_fabric_lane228': 'rx456:tx461',
      'lane_to_serdes_map_fabric_lane229': 'rx457:tx462',
      'lane_to_serdes_map_fabric_lane230': 'rx462:tx459',
      'lane_to_serdes_map_fabric_lane231': 'rx463:tx456',
      'lane_to_serdes_map_fabric_lane484': 'rx460:tx457',
      'lane_to_serdes_map_fabric_lane485': 'rx461:tx458',
      'lane_to_serdes_map_fabric_lane486': 'rx458:tx463',
      'lane_to_serdes_map_fabric_lane487': 'rx459:tx460',
      'lane_to_serdes_map_fabric_lane232': 'rx464:tx468',
      'lane_to_serdes_map_fabric_lane233': 'rx465:tx469',
      'lane_to_serdes_map_fabric_lane234': 'rx470:tx466',
      'lane_to_serdes_map_fabric_lane235': 'rx471:tx467',
      'lane_to_serdes_map_fabric_lane488': 'rx468:tx464',
      'lane_to_serdes_map_fabric_lane489': 'rx469:tx465',
      'lane_to_serdes_map_fabric_lane490': 'rx466:tx470',
      'lane_to_serdes_map_fabric_lane491': 'rx467:tx471',
      'lane_to_serdes_map_fabric_lane236': 'rx476:tx476',
      'lane_to_serdes_map_fabric_lane237': 'rx477:tx477',
      'lane_to_serdes_map_fabric_lane238': 'rx474:tx474',
      'lane_to_serdes_map_fabric_lane239': 'rx475:tx475',
      'lane_to_serdes_map_fabric_lane492': 'rx472:tx472',
      'lane_to_serdes_map_fabric_lane493': 'rx473:tx473',
      'lane_to_serdes_map_fabric_lane494': 'rx478:tx478',
      'lane_to_serdes_map_fabric_lane495': 'rx479:tx479',
      'lane_to_serdes_map_fabric_lane240': 'rx480:tx481',
      'lane_to_serdes_map_fabric_lane241': 'rx481:tx480',
      'lane_to_serdes_map_fabric_lane242': 'rx486:tx487',
      'lane_to_serdes_map_fabric_lane243': 'rx487:tx486',
      'lane_to_serdes_map_fabric_lane496': 'rx484:tx485',
      'lane_to_serdes_map_fabric_lane497': 'rx485:tx484',
      'lane_to_serdes_map_fabric_lane498': 'rx482:tx483',
      'lane_to_serdes_map_fabric_lane499': 'rx483:tx482',
      'lane_to_serdes_map_fabric_lane244': 'rx492:tx493',
      'lane_to_serdes_map_fabric_lane245': 'rx493:tx492',
      'lane_to_serdes_map_fabric_lane246': 'rx490:tx491',
      'lane_to_serdes_map_fabric_lane247': 'rx491:tx490',
      'lane_to_serdes_map_fabric_lane500': 'rx488:tx489',
      'lane_to_serdes_map_fabric_lane501': 'rx489:tx488',
      'lane_to_serdes_map_fabric_lane502': 'rx494:tx495',
      'lane_to_serdes_map_fabric_lane503': 'rx495:tx494',
      'lane_to_serdes_map_fabric_lane248': 'rx496:tx496',
      'lane_to_serdes_map_fabric_lane249': 'rx497:tx497',
      'lane_to_serdes_map_fabric_lane250': 'rx502:tx502',
      'lane_to_serdes_map_fabric_lane251': 'rx503:tx503',
      'lane_to_serdes_map_fabric_lane504': 'rx500:tx500',
      'lane_to_serdes_map_fabric_lane505': 'rx501:tx501',
      'lane_to_serdes_map_fabric_lane506': 'rx498:tx498',
      'lane_to_serdes_map_fabric_lane507': 'rx499:tx499',
      'lane_to_serdes_map_fabric_lane252': 'rx508:tx508',
      'lane_to_serdes_map_fabric_lane253': 'rx509:tx509',
      'lane_to_serdes_map_fabric_lane254': 'rx506:tx506',
      'lane_to_serdes_map_fabric_lane255': 'rx507:tx507',
      'lane_to_serdes_map_fabric_lane508': 'rx504:tx504',
      'lane_to_serdes_map_fabric_lane509': 'rx505:tx505',
      'lane_to_serdes_map_fabric_lane510': 'rx510:tx510',
      'lane_to_serdes_map_fabric_lane511': 'rx511:tx511',
   }
]

def wireAndApplyPolTraceLen( fes ):
   fes[0].cores[0].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[0].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[0].lanes[0].traceLengthToNextEpInInches = 7.82
   fes[0].cores[0].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[0].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[0].lanes[1].traceLengthToNextEpInInches = 10.04
   fes[0].cores[0].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[0].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[0].lanes[2].traceLengthToNextEpInInches = 11.75
   fes[0].cores[0].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[0].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[0].lanes[3].traceLengthToNextEpInInches = 13.84
   fes[0].cores[0].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[0].lanes[4].doTxPolaritySwapped = False
   fes[0].cores[0].lanes[4].traceLengthToNextEpInInches = 11.90
   fes[0].cores[0].lanes[5].doRxPolaritySwapped = False
   fes[0].cores[0].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[0].lanes[5].traceLengthToNextEpInInches = 14.00
   fes[0].cores[0].lanes[6].doRxPolaritySwapped = True
   fes[0].cores[0].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[0].lanes[6].traceLengthToNextEpInInches = 7.66
   fes[0].cores[0].lanes[7].doRxPolaritySwapped = True
   fes[0].cores[0].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[0].lanes[7].traceLengthToNextEpInInches = 9.88
   fes[0].cores[1].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[1].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[1].lanes[0].traceLengthToNextEpInInches = 7.49
   fes[0].cores[1].lanes[1].doRxPolaritySwapped = True
   fes[0].cores[1].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[1].lanes[1].traceLengthToNextEpInInches = 9.74
   fes[0].cores[1].lanes[2].doRxPolaritySwapped = False
   fes[0].cores[1].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[1].lanes[2].traceLengthToNextEpInInches = 12.03
   fes[0].cores[1].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[1].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[1].lanes[3].traceLengthToNextEpInInches = 14.17
   fes[0].cores[1].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[1].lanes[4].doTxPolaritySwapped = False
   fes[0].cores[1].lanes[4].traceLengthToNextEpInInches = 12.18
   fes[0].cores[1].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[1].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[1].lanes[5].traceLengthToNextEpInInches = 14.33
   fes[0].cores[1].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[1].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[1].lanes[6].traceLengthToNextEpInInches = 7.33
   fes[0].cores[1].lanes[7].doRxPolaritySwapped = True
   fes[0].cores[1].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[1].lanes[7].traceLengthToNextEpInInches = 9.58
   fes[0].cores[2].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[2].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[2].lanes[0].traceLengthToNextEpInInches = 8.41
   fes[0].cores[2].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[2].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[2].lanes[1].traceLengthToNextEpInInches = 10.48
   fes[0].cores[2].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[2].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[2].lanes[2].traceLengthToNextEpInInches = 12.19
   fes[0].cores[2].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[2].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[2].lanes[3].traceLengthToNextEpInInches = 14.27
   fes[0].cores[2].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[2].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[2].lanes[4].traceLengthToNextEpInInches = 12.37
   fes[0].cores[2].lanes[5].doRxPolaritySwapped = False
   fes[0].cores[2].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[2].lanes[5].traceLengthToNextEpInInches = 14.43
   fes[0].cores[2].lanes[6].doRxPolaritySwapped = True
   fes[0].cores[2].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[2].lanes[6].traceLengthToNextEpInInches = 8.26
   fes[0].cores[2].lanes[7].doRxPolaritySwapped = True
   fes[0].cores[2].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[2].lanes[7].traceLengthToNextEpInInches = 10.33
   fes[0].cores[3].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[3].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[3].lanes[0].traceLengthToNextEpInInches = 8.10
   fes[0].cores[3].lanes[1].doRxPolaritySwapped = True
   fes[0].cores[3].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[3].lanes[1].traceLengthToNextEpInInches = 10.18
   fes[0].cores[3].lanes[2].doRxPolaritySwapped = False
   fes[0].cores[3].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[3].lanes[2].traceLengthToNextEpInInches = 12.51
   fes[0].cores[3].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[3].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[3].lanes[3].traceLengthToNextEpInInches = 14.58
   fes[0].cores[3].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[3].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[3].lanes[4].traceLengthToNextEpInInches = 12.66
   fes[0].cores[3].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[3].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[3].lanes[5].traceLengthToNextEpInInches = 14.75
   fes[0].cores[3].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[3].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[3].lanes[6].traceLengthToNextEpInInches = 7.89
   fes[0].cores[3].lanes[7].doRxPolaritySwapped = True
   fes[0].cores[3].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[3].lanes[7].traceLengthToNextEpInInches = 9.96
   fes[0].cores[4].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[4].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[4].lanes[0].traceLengthToNextEpInInches = 5.50
   fes[0].cores[4].lanes[1].doRxPolaritySwapped = True
   fes[0].cores[4].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[4].lanes[1].traceLengthToNextEpInInches = 7.72
   fes[0].cores[4].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[4].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[4].lanes[2].traceLengthToNextEpInInches = 9.62
   fes[0].cores[4].lanes[3].doRxPolaritySwapped = False
   fes[0].cores[4].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[4].lanes[3].traceLengthToNextEpInInches = 11.79
   fes[0].cores[4].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[4].lanes[4].doTxPolaritySwapped = False
   fes[0].cores[4].lanes[4].traceLengthToNextEpInInches = 5.41
   fes[0].cores[4].lanes[5].doRxPolaritySwapped = False
   fes[0].cores[4].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[4].lanes[5].traceLengthToNextEpInInches = 7.55
   fes[0].cores[4].lanes[6].doRxPolaritySwapped = True
   fes[0].cores[4].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[4].lanes[6].traceLengthToNextEpInInches = 9.61
   fes[0].cores[4].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[4].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[4].lanes[7].traceLengthToNextEpInInches = 11.87
   fes[0].cores[5].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[5].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[5].lanes[0].traceLengthToNextEpInInches = 5.15
   fes[0].cores[5].lanes[1].doRxPolaritySwapped = True
   fes[0].cores[5].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[5].lanes[1].traceLengthToNextEpInInches = 7.48
   fes[0].cores[5].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[5].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[5].lanes[2].traceLengthToNextEpInInches = 9.66
   fes[0].cores[5].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[5].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[5].lanes[3].traceLengthToNextEpInInches = 11.59
   fes[0].cores[5].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[5].lanes[4].doTxPolaritySwapped = False
   fes[0].cores[5].lanes[4].traceLengthToNextEpInInches = 5.15
   fes[0].cores[5].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[5].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[5].lanes[5].traceLengthToNextEpInInches = 7.36
   fes[0].cores[5].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[5].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[5].lanes[6].traceLengthToNextEpInInches = 9.60
   fes[0].cores[5].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[5].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[5].lanes[7].traceLengthToNextEpInInches = 11.85
   fes[0].cores[6].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[6].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[6].lanes[0].traceLengthToNextEpInInches = 6.21
   fes[0].cores[6].lanes[1].doRxPolaritySwapped = True
   fes[0].cores[6].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[6].lanes[1].traceLengthToNextEpInInches = 8.35
   fes[0].cores[6].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[6].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[6].lanes[2].traceLengthToNextEpInInches = 10.47
   fes[0].cores[6].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[6].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[6].lanes[3].traceLengthToNextEpInInches = 12.45
   fes[0].cores[6].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[6].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[6].lanes[4].traceLengthToNextEpInInches = 6.22
   fes[0].cores[6].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[6].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[6].lanes[5].traceLengthToNextEpInInches = 8.31
   fes[0].cores[6].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[6].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[6].lanes[6].traceLengthToNextEpInInches = 10.59
   fes[0].cores[6].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[6].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[6].lanes[7].traceLengthToNextEpInInches = 12.63
   fes[0].cores[7].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[7].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[7].lanes[0].traceLengthToNextEpInInches = 6.06
   fes[0].cores[7].lanes[1].doRxPolaritySwapped = True
   fes[0].cores[7].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[7].lanes[1].traceLengthToNextEpInInches = 8.19
   fes[0].cores[7].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[7].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[7].lanes[2].traceLengthToNextEpInInches = 10.31
   fes[0].cores[7].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[7].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[7].lanes[3].traceLengthToNextEpInInches = 12.28
   fes[0].cores[7].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[7].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[7].lanes[4].traceLengthToNextEpInInches = 6.07
   fes[0].cores[7].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[7].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[7].lanes[5].traceLengthToNextEpInInches = 8.16
   fes[0].cores[7].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[7].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[7].lanes[6].traceLengthToNextEpInInches = 10.43
   fes[0].cores[7].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[7].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[7].lanes[7].traceLengthToNextEpInInches = 12.45
   fes[0].cores[8].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[8].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[8].lanes[0].traceLengthToNextEpInInches = 4.60
   fes[0].cores[8].lanes[1].doRxPolaritySwapped = True
   fes[0].cores[8].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[8].lanes[1].traceLengthToNextEpInInches = 6.94
   fes[0].cores[8].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[8].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[8].lanes[2].traceLengthToNextEpInInches = 9.12
   fes[0].cores[8].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[8].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[8].lanes[3].traceLengthToNextEpInInches = 11.06
   fes[0].cores[8].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[8].lanes[4].doTxPolaritySwapped = False
   fes[0].cores[8].lanes[4].traceLengthToNextEpInInches = 4.60
   fes[0].cores[8].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[8].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[8].lanes[5].traceLengthToNextEpInInches = 6.81
   fes[0].cores[8].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[8].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[8].lanes[6].traceLengthToNextEpInInches = 9.06
   fes[0].cores[8].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[8].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[8].lanes[7].traceLengthToNextEpInInches = 11.32
   fes[0].cores[9].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[9].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[9].lanes[0].traceLengthToNextEpInInches = 4.43
   fes[0].cores[9].lanes[1].doRxPolaritySwapped = True
   fes[0].cores[9].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[9].lanes[1].traceLengthToNextEpInInches = 6.78
   fes[0].cores[9].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[9].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[9].lanes[2].traceLengthToNextEpInInches = 8.97
   fes[0].cores[9].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[9].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[9].lanes[3].traceLengthToNextEpInInches = 10.90
   fes[0].cores[9].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[9].lanes[4].doTxPolaritySwapped = False
   fes[0].cores[9].lanes[4].traceLengthToNextEpInInches = 4.43
   fes[0].cores[9].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[9].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[9].lanes[5].traceLengthToNextEpInInches = 6.66
   fes[0].cores[9].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[9].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[9].lanes[6].traceLengthToNextEpInInches = 8.91
   fes[0].cores[9].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[9].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[9].lanes[7].traceLengthToNextEpInInches = 11.16
   fes[0].cores[10].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[10].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[10].lanes[0].traceLengthToNextEpInInches = 5.52
   fes[0].cores[10].lanes[1].doRxPolaritySwapped = True
   fes[0].cores[10].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[10].lanes[1].traceLengthToNextEpInInches = 7.65
   fes[0].cores[10].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[10].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[10].lanes[2].traceLengthToNextEpInInches = 9.77
   fes[0].cores[10].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[10].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[10].lanes[3].traceLengthToNextEpInInches = 11.75
   fes[0].cores[10].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[10].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[10].lanes[4].traceLengthToNextEpInInches = 5.52
   fes[0].cores[10].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[10].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[10].lanes[5].traceLengthToNextEpInInches = 7.61
   fes[0].cores[10].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[10].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[10].lanes[6].traceLengthToNextEpInInches = 9.89
   fes[0].cores[10].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[10].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[10].lanes[7].traceLengthToNextEpInInches = 11.93
   fes[0].cores[11].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[11].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[11].lanes[0].traceLengthToNextEpInInches = 5.36
   fes[0].cores[11].lanes[1].doRxPolaritySwapped = True
   fes[0].cores[11].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[11].lanes[1].traceLengthToNextEpInInches = 7.49
   fes[0].cores[11].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[11].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[11].lanes[2].traceLengthToNextEpInInches = 9.61
   fes[0].cores[11].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[11].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[11].lanes[3].traceLengthToNextEpInInches = 11.58
   fes[0].cores[11].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[11].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[11].lanes[4].traceLengthToNextEpInInches = 5.37
   fes[0].cores[11].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[11].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[11].lanes[5].traceLengthToNextEpInInches = 7.46
   fes[0].cores[11].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[11].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[11].lanes[6].traceLengthToNextEpInInches = 9.73
   fes[0].cores[11].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[11].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[11].lanes[7].traceLengthToNextEpInInches = 11.76
   fes[0].cores[12].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[12].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[12].lanes[0].traceLengthToNextEpInInches = 3.94
   fes[0].cores[12].lanes[1].doRxPolaritySwapped = True
   fes[0].cores[12].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[12].lanes[1].traceLengthToNextEpInInches = 6.28
   fes[0].cores[12].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[12].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[12].lanes[2].traceLengthToNextEpInInches = 8.47
   fes[0].cores[12].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[12].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[12].lanes[3].traceLengthToNextEpInInches = 10.41
   fes[0].cores[12].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[12].lanes[4].doTxPolaritySwapped = False
   fes[0].cores[12].lanes[4].traceLengthToNextEpInInches = 3.94
   fes[0].cores[12].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[12].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[12].lanes[5].traceLengthToNextEpInInches = 6.16
   fes[0].cores[12].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[12].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[12].lanes[6].traceLengthToNextEpInInches = 8.40
   fes[0].cores[12].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[12].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[12].lanes[7].traceLengthToNextEpInInches = 10.66
   fes[0].cores[13].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[13].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[13].lanes[0].traceLengthToNextEpInInches = 3.78
   fes[0].cores[13].lanes[1].doRxPolaritySwapped = True
   fes[0].cores[13].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[13].lanes[1].traceLengthToNextEpInInches = 6.13
   fes[0].cores[13].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[13].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[13].lanes[2].traceLengthToNextEpInInches = 8.32
   fes[0].cores[13].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[13].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[13].lanes[3].traceLengthToNextEpInInches = 10.26
   fes[0].cores[13].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[13].lanes[4].doTxPolaritySwapped = False
   fes[0].cores[13].lanes[4].traceLengthToNextEpInInches = 3.78
   fes[0].cores[13].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[13].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[13].lanes[5].traceLengthToNextEpInInches = 6.02
   fes[0].cores[13].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[13].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[13].lanes[6].traceLengthToNextEpInInches = 8.26
   fes[0].cores[13].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[13].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[13].lanes[7].traceLengthToNextEpInInches = 10.51
   fes[0].cores[14].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[14].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[14].lanes[0].traceLengthToNextEpInInches = 4.88
   fes[0].cores[14].lanes[1].doRxPolaritySwapped = True
   fes[0].cores[14].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[14].lanes[1].traceLengthToNextEpInInches = 7.01
   fes[0].cores[14].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[14].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[14].lanes[2].traceLengthToNextEpInInches = 9.13
   fes[0].cores[14].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[14].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[14].lanes[3].traceLengthToNextEpInInches = 11.07
   fes[0].cores[14].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[14].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[14].lanes[4].traceLengthToNextEpInInches = 4.89
   fes[0].cores[14].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[14].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[14].lanes[5].traceLengthToNextEpInInches = 6.98
   fes[0].cores[14].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[14].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[14].lanes[6].traceLengthToNextEpInInches = 9.25
   fes[0].cores[14].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[14].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[14].lanes[7].traceLengthToNextEpInInches = 11.25
   fes[0].cores[15].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[15].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[15].lanes[0].traceLengthToNextEpInInches = 4.73
   fes[0].cores[15].lanes[1].doRxPolaritySwapped = True
   fes[0].cores[15].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[15].lanes[1].traceLengthToNextEpInInches = 6.86
   fes[0].cores[15].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[15].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[15].lanes[2].traceLengthToNextEpInInches = 8.98
   fes[0].cores[15].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[15].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[15].lanes[3].traceLengthToNextEpInInches = 10.90
   fes[0].cores[15].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[15].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[15].lanes[4].traceLengthToNextEpInInches = 4.75
   fes[0].cores[15].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[15].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[15].lanes[5].traceLengthToNextEpInInches = 6.84
   fes[0].cores[15].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[15].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[15].lanes[6].traceLengthToNextEpInInches = 9.10
   fes[0].cores[15].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[15].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[15].lanes[7].traceLengthToNextEpInInches = 11.08
   fes[0].cores[16].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[16].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[16].lanes[0].traceLengthToNextEpInInches = 3.52
   fes[0].cores[16].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[16].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[16].lanes[1].traceLengthToNextEpInInches = 5.72
   fes[0].cores[16].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[16].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[16].lanes[2].traceLengthToNextEpInInches = 7.78
   fes[0].cores[16].lanes[3].doRxPolaritySwapped = False
   fes[0].cores[16].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[16].lanes[3].traceLengthToNextEpInInches = 9.99
   fes[0].cores[16].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[16].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[16].lanes[4].traceLengthToNextEpInInches = 3.30
   fes[0].cores[16].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[16].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[16].lanes[5].traceLengthToNextEpInInches = 5.70
   fes[0].cores[16].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[16].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[16].lanes[6].traceLengthToNextEpInInches = 7.94
   fes[0].cores[16].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[16].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[16].lanes[7].traceLengthToNextEpInInches = 9.88
   fes[0].cores[17].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[17].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[17].lanes[0].traceLengthToNextEpInInches = 3.33
   fes[0].cores[17].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[17].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[17].lanes[1].traceLengthToNextEpInInches = 5.55
   fes[0].cores[17].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[17].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[17].lanes[2].traceLengthToNextEpInInches = 7.61
   fes[0].cores[17].lanes[3].doRxPolaritySwapped = False
   fes[0].cores[17].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[17].lanes[3].traceLengthToNextEpInInches = 9.81
   fes[0].cores[17].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[17].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[17].lanes[4].traceLengthToNextEpInInches = 3.12
   fes[0].cores[17].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[17].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[17].lanes[5].traceLengthToNextEpInInches = 5.53
   fes[0].cores[17].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[17].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[17].lanes[6].traceLengthToNextEpInInches = 7.77
   fes[0].cores[17].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[17].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[17].lanes[7].traceLengthToNextEpInInches = 9.71
   fes[0].cores[18].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[18].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[18].lanes[0].traceLengthToNextEpInInches = 4.43
   fes[0].cores[18].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[18].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[18].lanes[1].traceLengthToNextEpInInches = 6.52
   fes[0].cores[18].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[18].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[18].lanes[2].traceLengthToNextEpInInches = 8.56
   fes[0].cores[18].lanes[3].doRxPolaritySwapped = False
   fes[0].cores[18].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[18].lanes[3].traceLengthToNextEpInInches = 10.58
   fes[0].cores[18].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[18].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[18].lanes[4].traceLengthToNextEpInInches = 4.27
   fes[0].cores[18].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[18].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[18].lanes[5].traceLengthToNextEpInInches = 6.35
   fes[0].cores[18].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[18].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[18].lanes[6].traceLengthToNextEpInInches = 8.58
   fes[0].cores[18].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[18].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[18].lanes[7].traceLengthToNextEpInInches = 10.53
   fes[0].cores[19].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[19].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[19].lanes[0].traceLengthToNextEpInInches = 4.28
   fes[0].cores[19].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[19].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[19].lanes[1].traceLengthToNextEpInInches = 6.37
   fes[0].cores[19].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[19].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[19].lanes[2].traceLengthToNextEpInInches = 8.41
   fes[0].cores[19].lanes[3].doRxPolaritySwapped = False
   fes[0].cores[19].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[19].lanes[3].traceLengthToNextEpInInches = 10.41
   fes[0].cores[19].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[19].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[19].lanes[4].traceLengthToNextEpInInches = 4.12
   fes[0].cores[19].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[19].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[19].lanes[5].traceLengthToNextEpInInches = 6.20
   fes[0].cores[19].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[19].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[19].lanes[6].traceLengthToNextEpInInches = 8.44
   fes[0].cores[19].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[19].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[19].lanes[7].traceLengthToNextEpInInches = 10.36
   fes[0].cores[20].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[20].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[20].lanes[0].traceLengthToNextEpInInches = 3.03
   fes[0].cores[20].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[20].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[20].lanes[1].traceLengthToNextEpInInches = 5.19
   fes[0].cores[20].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[20].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[20].lanes[2].traceLengthToNextEpInInches = 7.25
   fes[0].cores[20].lanes[3].doRxPolaritySwapped = False
   fes[0].cores[20].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[20].lanes[3].traceLengthToNextEpInInches = 9.46
   fes[0].cores[20].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[20].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[20].lanes[4].traceLengthToNextEpInInches = 2.82
   fes[0].cores[20].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[20].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[20].lanes[5].traceLengthToNextEpInInches = 5.17
   fes[0].cores[20].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[20].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[20].lanes[6].traceLengthToNextEpInInches = 7.41
   fes[0].cores[20].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[20].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[20].lanes[7].traceLengthToNextEpInInches = 9.34
   fes[0].cores[21].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[21].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[21].lanes[0].traceLengthToNextEpInInches = 2.78
   fes[0].cores[21].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[21].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[21].lanes[1].traceLengthToNextEpInInches = 5.05
   fes[0].cores[21].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[21].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[21].lanes[2].traceLengthToNextEpInInches = 7.11
   fes[0].cores[21].lanes[3].doRxPolaritySwapped = False
   fes[0].cores[21].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[21].lanes[3].traceLengthToNextEpInInches = 9.32
   fes[0].cores[21].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[21].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[21].lanes[4].traceLengthToNextEpInInches = 2.56
   fes[0].cores[21].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[21].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[21].lanes[5].traceLengthToNextEpInInches = 5.04
   fes[0].cores[21].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[21].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[21].lanes[6].traceLengthToNextEpInInches = 7.27
   fes[0].cores[21].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[21].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[21].lanes[7].traceLengthToNextEpInInches = 9.21
   fes[0].cores[22].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[22].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[22].lanes[0].traceLengthToNextEpInInches = 3.94
   fes[0].cores[22].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[22].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[22].lanes[1].traceLengthToNextEpInInches = 6.03
   fes[0].cores[22].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[22].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[22].lanes[2].traceLengthToNextEpInInches = 7.97
   fes[0].cores[22].lanes[3].doRxPolaritySwapped = False
   fes[0].cores[22].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[22].lanes[3].traceLengthToNextEpInInches = 10.03
   fes[0].cores[22].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[22].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[22].lanes[4].traceLengthToNextEpInInches = 3.68
   fes[0].cores[22].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[22].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[22].lanes[5].traceLengthToNextEpInInches = 5.76
   fes[0].cores[22].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[22].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[22].lanes[6].traceLengthToNextEpInInches = 8.10
   fes[0].cores[22].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[22].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[22].lanes[7].traceLengthToNextEpInInches = 9.97
   fes[0].cores[23].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[23].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[23].lanes[0].traceLengthToNextEpInInches = 3.70
   fes[0].cores[23].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[23].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[23].lanes[1].traceLengthToNextEpInInches = 5.78
   fes[0].cores[23].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[23].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[23].lanes[2].traceLengthToNextEpInInches = 7.84
   fes[0].cores[23].lanes[3].doRxPolaritySwapped = False
   fes[0].cores[23].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[23].lanes[3].traceLengthToNextEpInInches = 9.87
   fes[0].cores[23].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[23].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[23].lanes[4].traceLengthToNextEpInInches = 3.55
   fes[0].cores[23].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[23].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[23].lanes[5].traceLengthToNextEpInInches = 5.63
   fes[0].cores[23].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[23].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[23].lanes[6].traceLengthToNextEpInInches = 7.86
   fes[0].cores[23].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[23].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[23].lanes[7].traceLengthToNextEpInInches = 9.81
   fes[0].cores[24].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[24].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[24].lanes[0].traceLengthToNextEpInInches = 2.58
   fes[0].cores[24].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[24].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[24].lanes[1].traceLengthToNextEpInInches = 4.68
   fes[0].cores[24].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[24].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[24].lanes[2].traceLengthToNextEpInInches = 6.74
   fes[0].cores[24].lanes[3].doRxPolaritySwapped = False
   fes[0].cores[24].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[24].lanes[3].traceLengthToNextEpInInches = 8.96
   fes[0].cores[24].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[24].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[24].lanes[4].traceLengthToNextEpInInches = 2.37
   fes[0].cores[24].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[24].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[24].lanes[5].traceLengthToNextEpInInches = 4.67
   fes[0].cores[24].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[24].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[24].lanes[6].traceLengthToNextEpInInches = 6.90
   fes[0].cores[24].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[24].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[24].lanes[7].traceLengthToNextEpInInches = 8.84
   fes[0].cores[25].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[25].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[25].lanes[0].traceLengthToNextEpInInches = 2.43
   fes[0].cores[25].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[25].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[25].lanes[1].traceLengthToNextEpInInches = 4.55
   fes[0].cores[25].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[25].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[25].lanes[2].traceLengthToNextEpInInches = 6.61
   fes[0].cores[25].lanes[3].doRxPolaritySwapped = False
   fes[0].cores[25].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[25].lanes[3].traceLengthToNextEpInInches = 8.82
   fes[0].cores[25].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[25].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[25].lanes[4].traceLengthToNextEpInInches = 2.22
   fes[0].cores[25].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[25].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[25].lanes[5].traceLengthToNextEpInInches = 4.54
   fes[0].cores[25].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[25].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[25].lanes[6].traceLengthToNextEpInInches = 6.77
   fes[0].cores[25].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[25].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[25].lanes[7].traceLengthToNextEpInInches = 8.71
   fes[0].cores[26].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[26].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[26].lanes[0].traceLengthToNextEpInInches = 3.44
   fes[0].cores[26].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[26].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[26].lanes[1].traceLengthToNextEpInInches = 5.53
   fes[0].cores[26].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[26].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[26].lanes[2].traceLengthToNextEpInInches = 7.56
   fes[0].cores[26].lanes[3].doRxPolaritySwapped = False
   fes[0].cores[26].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[26].lanes[3].traceLengthToNextEpInInches = 9.67
   fes[0].cores[26].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[26].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[26].lanes[4].traceLengthToNextEpInInches = 3.28
   fes[0].cores[26].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[26].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[26].lanes[5].traceLengthToNextEpInInches = 5.37
   fes[0].cores[26].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[26].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[26].lanes[6].traceLengthToNextEpInInches = 7.59
   fes[0].cores[26].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[26].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[26].lanes[7].traceLengthToNextEpInInches = 9.61
   fes[0].cores[27].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[27].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[27].lanes[0].traceLengthToNextEpInInches = 3.05
   fes[0].cores[27].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[27].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[27].lanes[1].traceLengthToNextEpInInches = 5.18
   fes[0].cores[27].lanes[2].doRxPolaritySwapped = False
   fes[0].cores[27].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[27].lanes[2].traceLengthToNextEpInInches = 7.41
   fes[0].cores[27].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[27].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[27].lanes[3].traceLengthToNextEpInInches = 9.52
   fes[0].cores[27].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[27].lanes[4].doTxPolaritySwapped = False
   fes[0].cores[27].lanes[4].traceLengthToNextEpInInches = 3.03
   fes[0].cores[27].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[27].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[27].lanes[5].traceLengthToNextEpInInches = 5.07
   fes[0].cores[27].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[27].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[27].lanes[6].traceLengthToNextEpInInches = 7.34
   fes[0].cores[27].lanes[7].doRxPolaritySwapped = True
   fes[0].cores[27].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[27].lanes[7].traceLengthToNextEpInInches = 9.57
   fes[0].cores[28].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[28].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[28].lanes[0].traceLengthToNextEpInInches = 6.13
   fes[0].cores[28].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[28].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[28].lanes[1].traceLengthToNextEpInInches = 8.25
   fes[0].cores[28].lanes[2].doRxPolaritySwapped = False
   fes[0].cores[28].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[28].lanes[2].traceLengthToNextEpInInches = 1.90
   fes[0].cores[28].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[28].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[28].lanes[3].traceLengthToNextEpInInches = 4.01
   fes[0].cores[28].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[28].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[28].lanes[4].traceLengthToNextEpInInches = 1.89
   fes[0].cores[28].lanes[5].doRxPolaritySwapped = False
   fes[0].cores[28].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[28].lanes[5].traceLengthToNextEpInInches = 4.01
   fes[0].cores[28].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[28].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[28].lanes[6].traceLengthToNextEpInInches = 6.13
   fes[0].cores[28].lanes[7].doRxPolaritySwapped = True
   fes[0].cores[28].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[28].lanes[7].traceLengthToNextEpInInches = 8.25
   fes[0].cores[29].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[29].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[29].lanes[0].traceLengthToNextEpInInches = 6.15
   fes[0].cores[29].lanes[1].doRxPolaritySwapped = True
   fes[0].cores[29].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[29].lanes[1].traceLengthToNextEpInInches = 8.25
   fes[0].cores[29].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[29].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[29].lanes[2].traceLengthToNextEpInInches = 1.90
   fes[0].cores[29].lanes[3].doRxPolaritySwapped = False
   fes[0].cores[29].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[29].lanes[3].traceLengthToNextEpInInches = 3.99
   fes[0].cores[29].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[29].lanes[4].doTxPolaritySwapped = False
   fes[0].cores[29].lanes[4].traceLengthToNextEpInInches = 1.90
   fes[0].cores[29].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[29].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[29].lanes[5].traceLengthToNextEpInInches = 4.00
   fes[0].cores[29].lanes[6].doRxPolaritySwapped = True
   fes[0].cores[29].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[29].lanes[6].traceLengthToNextEpInInches = 6.16
   fes[0].cores[29].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[29].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[29].lanes[7].traceLengthToNextEpInInches = 8.26
   fes[0].cores[30].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[30].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[30].lanes[0].traceLengthToNextEpInInches = 7.28
   fes[0].cores[30].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[30].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[30].lanes[1].traceLengthToNextEpInInches = 9.29
   fes[0].cores[30].lanes[2].doRxPolaritySwapped = False
   fes[0].cores[30].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[30].lanes[2].traceLengthToNextEpInInches = 3.00
   fes[0].cores[30].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[30].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[30].lanes[3].traceLengthToNextEpInInches = 5.01
   fes[0].cores[30].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[30].lanes[4].doTxPolaritySwapped = False
   fes[0].cores[30].lanes[4].traceLengthToNextEpInInches = 3.00
   fes[0].cores[30].lanes[5].doRxPolaritySwapped = False
   fes[0].cores[30].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[30].lanes[5].traceLengthToNextEpInInches = 5.01
   fes[0].cores[30].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[30].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[30].lanes[6].traceLengthToNextEpInInches = 7.27
   fes[0].cores[30].lanes[7].doRxPolaritySwapped = True
   fes[0].cores[30].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[30].lanes[7].traceLengthToNextEpInInches = 9.29
   fes[0].cores[31].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[31].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[31].lanes[0].traceLengthToNextEpInInches = 7.28
   fes[0].cores[31].lanes[1].doRxPolaritySwapped = True
   fes[0].cores[31].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[31].lanes[1].traceLengthToNextEpInInches = 9.29
   fes[0].cores[31].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[31].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[31].lanes[2].traceLengthToNextEpInInches = 3.01
   fes[0].cores[31].lanes[3].doRxPolaritySwapped = False
   fes[0].cores[31].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[31].lanes[3].traceLengthToNextEpInInches = 5.02
   fes[0].cores[31].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[31].lanes[4].doTxPolaritySwapped = False
   fes[0].cores[31].lanes[4].traceLengthToNextEpInInches = 3.01
   fes[0].cores[31].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[31].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[31].lanes[5].traceLengthToNextEpInInches = 5.03
   fes[0].cores[31].lanes[6].doRxPolaritySwapped = True
   fes[0].cores[31].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[31].lanes[6].traceLengthToNextEpInInches = 7.27
   fes[0].cores[31].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[31].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[31].lanes[7].traceLengthToNextEpInInches = 9.29
   fes[0].cores[32].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[32].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[32].lanes[0].traceLengthToNextEpInInches = 1.90
   fes[0].cores[32].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[32].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[32].lanes[1].traceLengthToNextEpInInches = 4.01
   fes[0].cores[32].lanes[2].doRxPolaritySwapped = False
   fes[0].cores[32].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[32].lanes[2].traceLengthToNextEpInInches = 6.14
   fes[0].cores[32].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[32].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[32].lanes[3].traceLengthToNextEpInInches = 8.28
   fes[0].cores[32].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[32].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[32].lanes[4].traceLengthToNextEpInInches = 6.15
   fes[0].cores[32].lanes[5].doRxPolaritySwapped = False
   fes[0].cores[32].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[32].lanes[5].traceLengthToNextEpInInches = 8.29
   fes[0].cores[32].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[32].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[32].lanes[6].traceLengthToNextEpInInches = 1.89
   fes[0].cores[32].lanes[7].doRxPolaritySwapped = True
   fes[0].cores[32].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[32].lanes[7].traceLengthToNextEpInInches = 4.01
   fes[0].cores[33].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[33].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[33].lanes[0].traceLengthToNextEpInInches = 1.90
   fes[0].cores[33].lanes[1].doRxPolaritySwapped = True
   fes[0].cores[33].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[33].lanes[1].traceLengthToNextEpInInches = 4.04
   fes[0].cores[33].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[33].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[33].lanes[2].traceLengthToNextEpInInches = 6.12
   fes[0].cores[33].lanes[3].doRxPolaritySwapped = False
   fes[0].cores[33].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[33].lanes[3].traceLengthToNextEpInInches = 8.28
   fes[0].cores[33].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[33].lanes[4].doTxPolaritySwapped = False
   fes[0].cores[33].lanes[4].traceLengthToNextEpInInches = 6.12
   fes[0].cores[33].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[33].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[33].lanes[5].traceLengthToNextEpInInches = 8.28
   fes[0].cores[33].lanes[6].doRxPolaritySwapped = True
   fes[0].cores[33].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[33].lanes[6].traceLengthToNextEpInInches = 1.89
   fes[0].cores[33].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[33].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[33].lanes[7].traceLengthToNextEpInInches = 4.03
   fes[0].cores[34].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[34].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[34].lanes[0].traceLengthToNextEpInInches = 2.99
   fes[0].cores[34].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[34].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[34].lanes[1].traceLengthToNextEpInInches = 5.02
   fes[0].cores[34].lanes[2].doRxPolaritySwapped = False
   fes[0].cores[34].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[34].lanes[2].traceLengthToNextEpInInches = 7.24
   fes[0].cores[34].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[34].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[34].lanes[3].traceLengthToNextEpInInches = 9.29
   fes[0].cores[34].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[34].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[34].lanes[4].traceLengthToNextEpInInches = 7.25
   fes[0].cores[34].lanes[5].doRxPolaritySwapped = False
   fes[0].cores[34].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[34].lanes[5].traceLengthToNextEpInInches = 9.30
   fes[0].cores[34].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[34].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[34].lanes[6].traceLengthToNextEpInInches = 3.00
   fes[0].cores[34].lanes[7].doRxPolaritySwapped = True
   fes[0].cores[34].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[34].lanes[7].traceLengthToNextEpInInches = 5.02
   fes[0].cores[35].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[35].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[35].lanes[0].traceLengthToNextEpInInches = 3.01
   fes[0].cores[35].lanes[1].doRxPolaritySwapped = True
   fes[0].cores[35].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[35].lanes[1].traceLengthToNextEpInInches = 5.00
   fes[0].cores[35].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[35].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[35].lanes[2].traceLengthToNextEpInInches = 7.24
   fes[0].cores[35].lanes[3].doRxPolaritySwapped = False
   fes[0].cores[35].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[35].lanes[3].traceLengthToNextEpInInches = 9.30
   fes[0].cores[35].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[35].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[35].lanes[4].traceLengthToNextEpInInches = 7.23
   fes[0].cores[35].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[35].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[35].lanes[5].traceLengthToNextEpInInches = 9.30
   fes[0].cores[35].lanes[6].doRxPolaritySwapped = True
   fes[0].cores[35].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[35].lanes[6].traceLengthToNextEpInInches = 3.00
   fes[0].cores[35].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[35].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[35].lanes[7].traceLengthToNextEpInInches = 5.00
   fes[0].cores[36].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[36].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[36].lanes[0].traceLengthToNextEpInInches = 1.96
   fes[0].cores[36].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[36].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[36].lanes[1].traceLengthToNextEpInInches = 4.01
   fes[0].cores[36].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[36].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[36].lanes[2].traceLengthToNextEpInInches = 6.16
   fes[0].cores[36].lanes[3].doRxPolaritySwapped = False
   fes[0].cores[36].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[36].lanes[3].traceLengthToNextEpInInches = 8.50
   fes[0].cores[36].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[36].lanes[4].doTxPolaritySwapped = False
   fes[0].cores[36].lanes[4].traceLengthToNextEpInInches = 1.98
   fes[0].cores[36].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[36].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[36].lanes[5].traceLengthToNextEpInInches = 4.03
   fes[0].cores[36].lanes[6].doRxPolaritySwapped = True
   fes[0].cores[36].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[36].lanes[6].traceLengthToNextEpInInches = 6.22
   fes[0].cores[36].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[36].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[36].lanes[7].traceLengthToNextEpInInches = 8.39
   fes[0].cores[37].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[37].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[37].lanes[0].traceLengthToNextEpInInches = 1.98
   fes[0].cores[37].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[37].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[37].lanes[1].traceLengthToNextEpInInches = 4.33
   fes[0].cores[37].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[37].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[37].lanes[2].traceLengthToNextEpInInches = 6.57
   fes[0].cores[37].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[37].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[37].lanes[3].traceLengthToNextEpInInches = 8.53
   fes[0].cores[37].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[37].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[37].lanes[4].traceLengthToNextEpInInches = 2.18
   fes[0].cores[37].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[37].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[37].lanes[5].traceLengthToNextEpInInches = 4.36
   fes[0].cores[37].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[37].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[37].lanes[6].traceLengthToNextEpInInches = 6.42
   fes[0].cores[37].lanes[7].doRxPolaritySwapped = True
   fes[0].cores[37].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[37].lanes[7].traceLengthToNextEpInInches = 8.63
   fes[0].cores[38].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[38].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[38].lanes[0].traceLengthToNextEpInInches = 3.36
   fes[0].cores[38].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[38].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[38].lanes[1].traceLengthToNextEpInInches = 5.44
   fes[0].cores[38].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[38].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[38].lanes[2].traceLengthToNextEpInInches = 7.69
   fes[0].cores[38].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[38].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[38].lanes[3].traceLengthToNextEpInInches = 9.66
   fes[0].cores[38].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[38].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[38].lanes[4].traceLengthToNextEpInInches = 3.52
   fes[0].cores[38].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[38].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[38].lanes[5].traceLengthToNextEpInInches = 5.60
   fes[0].cores[38].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[38].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[38].lanes[6].traceLengthToNextEpInInches = 7.67
   fes[0].cores[38].lanes[7].doRxPolaritySwapped = True
   fes[0].cores[38].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[38].lanes[7].traceLengthToNextEpInInches = 9.73
   fes[0].cores[39].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[39].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[39].lanes[0].traceLengthToNextEpInInches = 3.50
   fes[0].cores[39].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[39].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[39].lanes[1].traceLengthToNextEpInInches = 5.58
   fes[0].cores[39].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[39].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[39].lanes[2].traceLengthToNextEpInInches = 7.83
   fes[0].cores[39].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[39].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[39].lanes[3].traceLengthToNextEpInInches = 9.79
   fes[0].cores[39].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[39].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[39].lanes[4].traceLengthToNextEpInInches = 3.67
   fes[0].cores[39].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[39].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[39].lanes[5].traceLengthToNextEpInInches = 5.74
   fes[0].cores[39].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[39].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[39].lanes[6].traceLengthToNextEpInInches = 7.81
   fes[0].cores[39].lanes[7].doRxPolaritySwapped = True
   fes[0].cores[39].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[39].lanes[7].traceLengthToNextEpInInches = 9.86
   fes[0].cores[40].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[40].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[40].lanes[0].traceLengthToNextEpInInches = 2.21
   fes[0].cores[40].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[40].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[40].lanes[1].traceLengthToNextEpInInches = 4.61
   fes[0].cores[40].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[40].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[40].lanes[2].traceLengthToNextEpInInches = 6.86
   fes[0].cores[40].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[40].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[40].lanes[3].traceLengthToNextEpInInches = 8.81
   fes[0].cores[40].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[40].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[40].lanes[4].traceLengthToNextEpInInches = 2.41
   fes[0].cores[40].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[40].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[40].lanes[5].traceLengthToNextEpInInches = 4.63
   fes[0].cores[40].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[40].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[40].lanes[6].traceLengthToNextEpInInches = 6.70
   fes[0].cores[40].lanes[7].doRxPolaritySwapped = True
   fes[0].cores[40].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[40].lanes[7].traceLengthToNextEpInInches = 8.91
   fes[0].cores[41].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[41].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[41].lanes[0].traceLengthToNextEpInInches = 2.35
   fes[0].cores[41].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[41].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[41].lanes[1].traceLengthToNextEpInInches = 4.75
   fes[0].cores[41].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[41].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[41].lanes[2].traceLengthToNextEpInInches = 7.10
   fes[0].cores[41].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[41].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[41].lanes[3].traceLengthToNextEpInInches = 9.05
   fes[0].cores[41].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[41].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[41].lanes[4].traceLengthToNextEpInInches = 2.56
   fes[0].cores[41].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[41].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[41].lanes[5].traceLengthToNextEpInInches = 4.88
   fes[0].cores[41].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[41].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[41].lanes[6].traceLengthToNextEpInInches = 6.84
   fes[0].cores[41].lanes[7].doRxPolaritySwapped = True
   fes[0].cores[41].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[41].lanes[7].traceLengthToNextEpInInches = 9.05
   fes[0].cores[42].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[42].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[42].lanes[0].traceLengthToNextEpInInches = 3.88
   fes[0].cores[42].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[42].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[42].lanes[1].traceLengthToNextEpInInches = 5.97
   fes[0].cores[42].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[42].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[42].lanes[2].traceLengthToNextEpInInches = 8.22
   fes[0].cores[42].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[42].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[42].lanes[3].traceLengthToNextEpInInches = 10.03
   fes[0].cores[42].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[42].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[42].lanes[4].traceLengthToNextEpInInches = 4.04
   fes[0].cores[42].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[42].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[42].lanes[5].traceLengthToNextEpInInches = 6.12
   fes[0].cores[42].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[42].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[42].lanes[6].traceLengthToNextEpInInches = 8.20
   fes[0].cores[42].lanes[7].doRxPolaritySwapped = True
   fes[0].cores[42].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[42].lanes[7].traceLengthToNextEpInInches = 10.09
   fes[0].cores[43].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[43].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[43].lanes[0].traceLengthToNextEpInInches = 4.02
   fes[0].cores[43].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[43].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[43].lanes[1].traceLengthToNextEpInInches = 6.10
   fes[0].cores[43].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[43].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[43].lanes[2].traceLengthToNextEpInInches = 8.36
   fes[0].cores[43].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[43].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[43].lanes[3].traceLengthToNextEpInInches = 10.19
   fes[0].cores[43].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[43].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[43].lanes[4].traceLengthToNextEpInInches = 4.18
   fes[0].cores[43].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[43].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[43].lanes[5].traceLengthToNextEpInInches = 6.26
   fes[0].cores[43].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[43].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[43].lanes[6].traceLengthToNextEpInInches = 8.33
   fes[0].cores[43].lanes[7].doRxPolaritySwapped = True
   fes[0].cores[43].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[43].lanes[7].traceLengthToNextEpInInches = 10.24
   fes[0].cores[44].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[44].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[44].lanes[0].traceLengthToNextEpInInches = 2.80
   fes[0].cores[44].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[44].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[44].lanes[1].traceLengthToNextEpInInches = 5.20
   fes[0].cores[44].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[44].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[44].lanes[2].traceLengthToNextEpInInches = 7.45
   fes[0].cores[44].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[44].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[44].lanes[3].traceLengthToNextEpInInches = 9.41
   fes[0].cores[44].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[44].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[44].lanes[4].traceLengthToNextEpInInches = 3.01
   fes[0].cores[44].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[44].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[44].lanes[5].traceLengthToNextEpInInches = 5.23
   fes[0].cores[44].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[44].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[44].lanes[6].traceLengthToNextEpInInches = 7.29
   fes[0].cores[44].lanes[7].doRxPolaritySwapped = True
   fes[0].cores[44].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[44].lanes[7].traceLengthToNextEpInInches = 9.50
   fes[0].cores[45].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[45].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[45].lanes[0].traceLengthToNextEpInInches = 2.96
   fes[0].cores[45].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[45].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[45].lanes[1].traceLengthToNextEpInInches = 5.35
   fes[0].cores[45].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[45].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[45].lanes[2].traceLengthToNextEpInInches = 7.60
   fes[0].cores[45].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[45].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[45].lanes[3].traceLengthToNextEpInInches = 9.55
   fes[0].cores[45].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[45].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[45].lanes[4].traceLengthToNextEpInInches = 3.17
   fes[0].cores[45].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[45].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[45].lanes[5].traceLengthToNextEpInInches = 5.39
   fes[0].cores[45].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[45].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[45].lanes[6].traceLengthToNextEpInInches = 7.43
   fes[0].cores[45].lanes[7].doRxPolaritySwapped = True
   fes[0].cores[45].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[45].lanes[7].traceLengthToNextEpInInches = 9.65
   fes[0].cores[46].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[46].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[46].lanes[0].traceLengthToNextEpInInches = 4.39
   fes[0].cores[46].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[46].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[46].lanes[1].traceLengthToNextEpInInches = 6.48
   fes[0].cores[46].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[46].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[46].lanes[2].traceLengthToNextEpInInches = 8.73
   fes[0].cores[46].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[46].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[46].lanes[3].traceLengthToNextEpInInches = 10.62
   fes[0].cores[46].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[46].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[46].lanes[4].traceLengthToNextEpInInches = 4.56
   fes[0].cores[46].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[46].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[46].lanes[5].traceLengthToNextEpInInches = 6.64
   fes[0].cores[46].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[46].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[46].lanes[6].traceLengthToNextEpInInches = 8.70
   fes[0].cores[46].lanes[7].doRxPolaritySwapped = True
   fes[0].cores[46].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[46].lanes[7].traceLengthToNextEpInInches = 10.67
   fes[0].cores[47].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[47].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[47].lanes[0].traceLengthToNextEpInInches = 4.56
   fes[0].cores[47].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[47].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[47].lanes[1].traceLengthToNextEpInInches = 6.64
   fes[0].cores[47].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[47].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[47].lanes[2].traceLengthToNextEpInInches = 8.91
   fes[0].cores[47].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[47].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[47].lanes[3].traceLengthToNextEpInInches = 10.80
   fes[0].cores[47].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[47].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[47].lanes[4].traceLengthToNextEpInInches = 4.73
   fes[0].cores[47].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[47].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[47].lanes[5].traceLengthToNextEpInInches = 6.81
   fes[0].cores[47].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[47].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[47].lanes[6].traceLengthToNextEpInInches = 8.87
   fes[0].cores[47].lanes[7].doRxPolaritySwapped = True
   fes[0].cores[47].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[47].lanes[7].traceLengthToNextEpInInches = 10.85
   fes[0].cores[48].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[48].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[48].lanes[0].traceLengthToNextEpInInches = 3.52
   fes[0].cores[48].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[48].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[48].lanes[1].traceLengthToNextEpInInches = 5.71
   fes[0].cores[48].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[48].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[48].lanes[2].traceLengthToNextEpInInches = 7.96
   fes[0].cores[48].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[48].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[48].lanes[3].traceLengthToNextEpInInches = 10.21
   fes[0].cores[48].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[48].lanes[4].doTxPolaritySwapped = False
   fes[0].cores[48].lanes[4].traceLengthToNextEpInInches = 3.51
   fes[0].cores[48].lanes[5].doRxPolaritySwapped = False
   fes[0].cores[48].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[48].lanes[5].traceLengthToNextEpInInches = 5.83
   fes[0].cores[48].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[48].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[48].lanes[6].traceLengthToNextEpInInches = 8.01
   fes[0].cores[48].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[48].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[48].lanes[7].traceLengthToNextEpInInches = 9.96
   fes[0].cores[49].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[49].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[49].lanes[0].traceLengthToNextEpInInches = 3.68
   fes[0].cores[49].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[49].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[49].lanes[1].traceLengthToNextEpInInches = 5.86
   fes[0].cores[49].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[49].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[49].lanes[2].traceLengthToNextEpInInches = 8.11
   fes[0].cores[49].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[49].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[49].lanes[3].traceLengthToNextEpInInches = 10.36
   fes[0].cores[49].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[49].lanes[4].doTxPolaritySwapped = False
   fes[0].cores[49].lanes[4].traceLengthToNextEpInInches = 3.67
   fes[0].cores[49].lanes[5].doRxPolaritySwapped = False
   fes[0].cores[49].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[49].lanes[5].traceLengthToNextEpInInches = 5.98
   fes[0].cores[49].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[49].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[49].lanes[6].traceLengthToNextEpInInches = 8.16
   fes[0].cores[49].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[49].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[49].lanes[7].traceLengthToNextEpInInches = 10.11
   fes[0].cores[50].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[50].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[50].lanes[0].traceLengthToNextEpInInches = 5.03
   fes[0].cores[50].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[50].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[50].lanes[1].traceLengthToNextEpInInches = 7.11
   fes[0].cores[50].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[50].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[50].lanes[2].traceLengthToNextEpInInches = 9.41
   fes[0].cores[50].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[50].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[50].lanes[3].traceLengthToNextEpInInches = 11.38
   fes[0].cores[50].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[50].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[50].lanes[4].traceLengthToNextEpInInches = 5.02
   fes[0].cores[50].lanes[5].doRxPolaritySwapped = False
   fes[0].cores[50].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[50].lanes[5].traceLengthToNextEpInInches = 7.14
   fes[0].cores[50].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[50].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[50].lanes[6].traceLengthToNextEpInInches = 9.29
   fes[0].cores[50].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[50].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[50].lanes[7].traceLengthToNextEpInInches = 11.21
   fes[0].cores[51].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[51].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[51].lanes[0].traceLengthToNextEpInInches = 5.19
   fes[0].cores[51].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[51].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[51].lanes[1].traceLengthToNextEpInInches = 7.26
   fes[0].cores[51].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[51].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[51].lanes[2].traceLengthToNextEpInInches = 9.56
   fes[0].cores[51].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[51].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[51].lanes[3].traceLengthToNextEpInInches = 11.54
   fes[0].cores[51].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[51].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[51].lanes[4].traceLengthToNextEpInInches = 5.17
   fes[0].cores[51].lanes[5].doRxPolaritySwapped = False
   fes[0].cores[51].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[51].lanes[5].traceLengthToNextEpInInches = 7.29
   fes[0].cores[51].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[51].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[51].lanes[6].traceLengthToNextEpInInches = 9.43
   fes[0].cores[51].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[51].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[51].lanes[7].traceLengthToNextEpInInches = 11.37
   fes[0].cores[52].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[52].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[52].lanes[0].traceLengthToNextEpInInches = 4.21
   fes[0].cores[52].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[52].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[52].lanes[1].traceLengthToNextEpInInches = 6.35
   fes[0].cores[52].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[52].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[52].lanes[2].traceLengthToNextEpInInches = 8.61
   fes[0].cores[52].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[52].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[52].lanes[3].traceLengthToNextEpInInches = 10.86
   fes[0].cores[52].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[52].lanes[4].doTxPolaritySwapped = False
   fes[0].cores[52].lanes[4].traceLengthToNextEpInInches = 4.20
   fes[0].cores[52].lanes[5].doRxPolaritySwapped = False
   fes[0].cores[52].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[52].lanes[5].traceLengthToNextEpInInches = 6.47
   fes[0].cores[52].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[52].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[52].lanes[6].traceLengthToNextEpInInches = 8.66
   fes[0].cores[52].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[52].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[52].lanes[7].traceLengthToNextEpInInches = 10.61
   fes[0].cores[53].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[53].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[53].lanes[0].traceLengthToNextEpInInches = 4.37
   fes[0].cores[53].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[53].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[53].lanes[1].traceLengthToNextEpInInches = 6.50
   fes[0].cores[53].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[53].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[53].lanes[2].traceLengthToNextEpInInches = 8.76
   fes[0].cores[53].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[53].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[53].lanes[3].traceLengthToNextEpInInches = 11.01
   fes[0].cores[53].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[53].lanes[4].doTxPolaritySwapped = False
   fes[0].cores[53].lanes[4].traceLengthToNextEpInInches = 4.36
   fes[0].cores[53].lanes[5].doRxPolaritySwapped = False
   fes[0].cores[53].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[53].lanes[5].traceLengthToNextEpInInches = 6.63
   fes[0].cores[53].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[53].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[53].lanes[6].traceLengthToNextEpInInches = 8.81
   fes[0].cores[53].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[53].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[53].lanes[7].traceLengthToNextEpInInches = 10.76
   fes[0].cores[54].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[54].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[54].lanes[0].traceLengthToNextEpInInches = 5.68
   fes[0].cores[54].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[54].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[54].lanes[1].traceLengthToNextEpInInches = 7.76
   fes[0].cores[54].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[54].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[54].lanes[2].traceLengthToNextEpInInches = 10.07
   fes[0].cores[54].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[54].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[54].lanes[3].traceLengthToNextEpInInches = 12.05
   fes[0].cores[54].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[54].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[54].lanes[4].traceLengthToNextEpInInches = 5.67
   fes[0].cores[54].lanes[5].doRxPolaritySwapped = False
   fes[0].cores[54].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[54].lanes[5].traceLengthToNextEpInInches = 7.80
   fes[0].cores[54].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[54].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[54].lanes[6].traceLengthToNextEpInInches = 9.94
   fes[0].cores[54].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[54].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[54].lanes[7].traceLengthToNextEpInInches = 11.88
   fes[0].cores[55].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[55].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[55].lanes[0].traceLengthToNextEpInInches = 5.84
   fes[0].cores[55].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[55].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[55].lanes[1].traceLengthToNextEpInInches = 7.92
   fes[0].cores[55].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[55].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[55].lanes[2].traceLengthToNextEpInInches = 10.23
   fes[0].cores[55].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[55].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[55].lanes[3].traceLengthToNextEpInInches = 12.22
   fes[0].cores[55].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[55].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[55].lanes[4].traceLengthToNextEpInInches = 5.83
   fes[0].cores[55].lanes[5].doRxPolaritySwapped = False
   fes[0].cores[55].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[55].lanes[5].traceLengthToNextEpInInches = 7.95
   fes[0].cores[55].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[55].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[55].lanes[6].traceLengthToNextEpInInches = 10.09
   fes[0].cores[55].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[55].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[55].lanes[7].traceLengthToNextEpInInches = 12.05
   fes[0].cores[56].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[56].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[56].lanes[0].traceLengthToNextEpInInches = 4.94
   fes[0].cores[56].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[56].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[56].lanes[1].traceLengthToNextEpInInches = 7.04
   fes[0].cores[56].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[56].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[56].lanes[2].traceLengthToNextEpInInches = 9.31
   fes[0].cores[56].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[56].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[56].lanes[3].traceLengthToNextEpInInches = 11.57
   fes[0].cores[56].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[56].lanes[4].doTxPolaritySwapped = False
   fes[0].cores[56].lanes[4].traceLengthToNextEpInInches = 4.92
   fes[0].cores[56].lanes[5].doRxPolaritySwapped = False
   fes[0].cores[56].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[56].lanes[5].traceLengthToNextEpInInches = 7.16
   fes[0].cores[56].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[56].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[56].lanes[6].traceLengthToNextEpInInches = 9.36
   fes[0].cores[56].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[56].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[56].lanes[7].traceLengthToNextEpInInches = 11.32
   fes[0].cores[57].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[57].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[57].lanes[0].traceLengthToNextEpInInches = 5.10
   fes[0].cores[57].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[57].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[57].lanes[1].traceLengthToNextEpInInches = 7.20
   fes[0].cores[57].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[57].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[57].lanes[2].traceLengthToNextEpInInches = 9.46
   fes[0].cores[57].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[57].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[57].lanes[3].traceLengthToNextEpInInches = 11.72
   fes[0].cores[57].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[57].lanes[4].doTxPolaritySwapped = False
   fes[0].cores[57].lanes[4].traceLengthToNextEpInInches = 5.09
   fes[0].cores[57].lanes[5].doRxPolaritySwapped = False
   fes[0].cores[57].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[57].lanes[5].traceLengthToNextEpInInches = 7.32
   fes[0].cores[57].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[57].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[57].lanes[6].traceLengthToNextEpInInches = 9.51
   fes[0].cores[57].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[57].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[57].lanes[7].traceLengthToNextEpInInches = 11.46
   fes[0].cores[58].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[58].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[58].lanes[0].traceLengthToNextEpInInches = 6.38
   fes[0].cores[58].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[58].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[58].lanes[1].traceLengthToNextEpInInches = 8.46
   fes[0].cores[58].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[58].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[58].lanes[2].traceLengthToNextEpInInches = 10.77
   fes[0].cores[58].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[58].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[58].lanes[3].traceLengthToNextEpInInches = 12.76
   fes[0].cores[58].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[58].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[58].lanes[4].traceLengthToNextEpInInches = 6.36
   fes[0].cores[58].lanes[5].doRxPolaritySwapped = False
   fes[0].cores[58].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[58].lanes[5].traceLengthToNextEpInInches = 8.49
   fes[0].cores[58].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[58].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[58].lanes[6].traceLengthToNextEpInInches = 10.65
   fes[0].cores[58].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[58].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[58].lanes[7].traceLengthToNextEpInInches = 12.60
   fes[0].cores[59].lanes[0].doRxPolaritySwapped = False
   fes[0].cores[59].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[59].lanes[0].traceLengthToNextEpInInches = 6.40
   fes[0].cores[59].lanes[1].doRxPolaritySwapped = True
   fes[0].cores[59].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[59].lanes[1].traceLengthToNextEpInInches = 8.70
   fes[0].cores[59].lanes[2].doRxPolaritySwapped = False
   fes[0].cores[59].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[59].lanes[2].traceLengthToNextEpInInches = 10.75
   fes[0].cores[59].lanes[3].doRxPolaritySwapped = True
   fes[0].cores[59].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[59].lanes[3].traceLengthToNextEpInInches = 13.03
   fes[0].cores[59].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[59].lanes[4].doTxPolaritySwapped = False
   fes[0].cores[59].lanes[4].traceLengthToNextEpInInches = 6.57
   fes[0].cores[59].lanes[5].doRxPolaritySwapped = False
   fes[0].cores[59].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[59].lanes[5].traceLengthToNextEpInInches = 8.69
   fes[0].cores[59].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[59].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[59].lanes[6].traceLengthToNextEpInInches = 10.67
   fes[0].cores[59].lanes[7].doRxPolaritySwapped = True
   fes[0].cores[59].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[59].lanes[7].traceLengthToNextEpInInches = 12.94
   fes[0].cores[60].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[60].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[60].lanes[0].traceLengthToNextEpInInches = 11.60
   fes[0].cores[60].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[60].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[60].lanes[1].traceLengthToNextEpInInches = 13.74
   fes[0].cores[60].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[60].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[60].lanes[2].traceLengthToNextEpInInches = 6.87
   fes[0].cores[60].lanes[3].doRxPolaritySwapped = False
   fes[0].cores[60].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[60].lanes[3].traceLengthToNextEpInInches = 8.94
   fes[0].cores[60].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[60].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[60].lanes[4].traceLengthToNextEpInInches = 7.02
   fes[0].cores[60].lanes[5].doRxPolaritySwapped = False
   fes[0].cores[60].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[60].lanes[5].traceLengthToNextEpInInches = 9.14
   fes[0].cores[60].lanes[6].doRxPolaritySwapped = True
   fes[0].cores[60].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[60].lanes[6].traceLengthToNextEpInInches = 11.46
   fes[0].cores[60].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[60].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[60].lanes[7].traceLengthToNextEpInInches = 13.59
   fes[0].cores[61].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[61].lanes[0].doTxPolaritySwapped = True
   fes[0].cores[61].lanes[0].traceLengthToNextEpInInches = 11.32
   fes[0].cores[61].lanes[1].doRxPolaritySwapped = True
   fes[0].cores[61].lanes[1].doTxPolaritySwapped = False
   fes[0].cores[61].lanes[1].traceLengthToNextEpInInches = 13.44
   fes[0].cores[61].lanes[2].doRxPolaritySwapped = False
   fes[0].cores[61].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[61].lanes[2].traceLengthToNextEpInInches = 7.19
   fes[0].cores[61].lanes[3].doRxPolaritySwapped = False
   fes[0].cores[61].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[61].lanes[3].traceLengthToNextEpInInches = 9.28
   fes[0].cores[61].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[61].lanes[4].doTxPolaritySwapped = True
   fes[0].cores[61].lanes[4].traceLengthToNextEpInInches = 7.33
   fes[0].cores[61].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[61].lanes[5].doTxPolaritySwapped = False
   fes[0].cores[61].lanes[5].traceLengthToNextEpInInches = 9.42
   fes[0].cores[61].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[61].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[61].lanes[6].traceLengthToNextEpInInches = 11.13
   fes[0].cores[61].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[61].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[61].lanes[7].traceLengthToNextEpInInches = 13.26
   fes[0].cores[62].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[62].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[62].lanes[0].traceLengthToNextEpInInches = 13.30
   fes[0].cores[62].lanes[1].doRxPolaritySwapped = False
   fes[0].cores[62].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[62].lanes[1].traceLengthToNextEpInInches = 15.23
   fes[0].cores[62].lanes[2].doRxPolaritySwapped = True
   fes[0].cores[62].lanes[2].doTxPolaritySwapped = True
   fes[0].cores[62].lanes[2].traceLengthToNextEpInInches = 8.56
   fes[0].cores[62].lanes[3].doRxPolaritySwapped = False
   fes[0].cores[62].lanes[3].doTxPolaritySwapped = False
   fes[0].cores[62].lanes[3].traceLengthToNextEpInInches = 10.62
   fes[0].cores[62].lanes[4].doRxPolaritySwapped = True
   fes[0].cores[62].lanes[4].doTxPolaritySwapped = False
   fes[0].cores[62].lanes[4].traceLengthToNextEpInInches = 8.71
   fes[0].cores[62].lanes[5].doRxPolaritySwapped = False
   fes[0].cores[62].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[62].lanes[5].traceLengthToNextEpInInches = 10.76
   fes[0].cores[62].lanes[6].doRxPolaritySwapped = True
   fes[0].cores[62].lanes[6].doTxPolaritySwapped = True
   fes[0].cores[62].lanes[6].traceLengthToNextEpInInches = 13.14
   fes[0].cores[62].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[62].lanes[7].doTxPolaritySwapped = False
   fes[0].cores[62].lanes[7].traceLengthToNextEpInInches = 15.09
   fes[0].cores[63].lanes[0].doRxPolaritySwapped = True
   fes[0].cores[63].lanes[0].doTxPolaritySwapped = False
   fes[0].cores[63].lanes[0].traceLengthToNextEpInInches = 12.99
   fes[0].cores[63].lanes[1].doRxPolaritySwapped = True
   fes[0].cores[63].lanes[1].doTxPolaritySwapped = True
   fes[0].cores[63].lanes[1].traceLengthToNextEpInInches = 14.94
   fes[0].cores[63].lanes[2].doRxPolaritySwapped = False
   fes[0].cores[63].lanes[2].doTxPolaritySwapped = False
   fes[0].cores[63].lanes[2].traceLengthToNextEpInInches = 8.86
   fes[0].cores[63].lanes[3].doRxPolaritySwapped = False
   fes[0].cores[63].lanes[3].doTxPolaritySwapped = True
   fes[0].cores[63].lanes[3].traceLengthToNextEpInInches = 10.92
   fes[0].cores[63].lanes[4].doRxPolaritySwapped = False
   fes[0].cores[63].lanes[4].doTxPolaritySwapped = False
   fes[0].cores[63].lanes[4].traceLengthToNextEpInInches = 9.00
   fes[0].cores[63].lanes[5].doRxPolaritySwapped = True
   fes[0].cores[63].lanes[5].doTxPolaritySwapped = True
   fes[0].cores[63].lanes[5].traceLengthToNextEpInInches = 11.07
   fes[0].cores[63].lanes[6].doRxPolaritySwapped = False
   fes[0].cores[63].lanes[6].doTxPolaritySwapped = False
   fes[0].cores[63].lanes[6].traceLengthToNextEpInInches = 12.85
   fes[0].cores[63].lanes[7].doRxPolaritySwapped = False
   fes[0].cores[63].lanes[7].doTxPolaritySwapped = True
   fes[0].cores[63].lanes[7].traceLengthToNextEpInInches = 14.80
   fes[1].cores[0].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[0].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[0].lanes[0].traceLengthToNextEpInInches = 9.84
   fes[1].cores[0].lanes[1].doRxPolaritySwapped = True
   fes[1].cores[0].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[0].lanes[1].traceLengthToNextEpInInches = 7.43
   fes[1].cores[0].lanes[2].doRxPolaritySwapped = False
   fes[1].cores[0].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[0].lanes[2].traceLengthToNextEpInInches = 14.20
   fes[1].cores[0].lanes[3].doRxPolaritySwapped = False
   fes[1].cores[0].lanes[3].doTxPolaritySwapped = False
   fes[1].cores[0].lanes[3].traceLengthToNextEpInInches = 12.05
   fes[1].cores[0].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[0].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[0].lanes[4].traceLengthToNextEpInInches = 14.35
   fes[1].cores[0].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[0].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[0].lanes[5].traceLengthToNextEpInInches = 12.20
   fes[1].cores[0].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[0].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[0].lanes[6].traceLengthToNextEpInInches = 9.69
   fes[1].cores[0].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[0].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[0].lanes[7].traceLengthToNextEpInInches = 7.27
   fes[1].cores[1].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[1].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[1].lanes[0].traceLengthToNextEpInInches = 10.13
   fes[1].cores[1].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[1].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[1].lanes[1].traceLengthToNextEpInInches = 7.82
   fes[1].cores[1].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[1].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[1].lanes[2].traceLengthToNextEpInInches = 13.90
   fes[1].cores[1].lanes[3].doRxPolaritySwapped = False
   fes[1].cores[1].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[1].lanes[3].traceLengthToNextEpInInches = 11.76
   fes[1].cores[1].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[1].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[1].lanes[4].traceLengthToNextEpInInches = 14.04
   fes[1].cores[1].lanes[5].doRxPolaritySwapped = False
   fes[1].cores[1].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[1].lanes[5].traceLengthToNextEpInInches = 11.91
   fes[1].cores[1].lanes[6].doRxPolaritySwapped = True
   fes[1].cores[1].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[1].lanes[6].traceLengthToNextEpInInches = 9.98
   fes[1].cores[1].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[1].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[1].lanes[7].traceLengthToNextEpInInches = 7.66
   fes[1].cores[2].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[2].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[2].lanes[0].traceLengthToNextEpInInches = 10.28
   fes[1].cores[2].lanes[1].doRxPolaritySwapped = True
   fes[1].cores[2].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[2].lanes[1].traceLengthToNextEpInInches = 8.11
   fes[1].cores[2].lanes[2].doRxPolaritySwapped = False
   fes[1].cores[2].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[2].lanes[2].traceLengthToNextEpInInches = 14.62
   fes[1].cores[2].lanes[3].doRxPolaritySwapped = False
   fes[1].cores[2].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[2].lanes[3].traceLengthToNextEpInInches = 12.50
   fes[1].cores[2].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[2].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[2].lanes[4].traceLengthToNextEpInInches = 14.78
   fes[1].cores[2].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[2].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[2].lanes[5].traceLengthToNextEpInInches = 12.66
   fes[1].cores[2].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[2].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[2].lanes[6].traceLengthToNextEpInInches = 10.07
   fes[1].cores[2].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[2].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[2].lanes[7].traceLengthToNextEpInInches = 7.91
   fes[1].cores[3].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[3].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[3].lanes[0].traceLengthToNextEpInInches = 10.59
   fes[1].cores[3].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[3].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[3].lanes[1].traceLengthToNextEpInInches = 8.41
   fes[1].cores[3].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[3].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[3].lanes[2].traceLengthToNextEpInInches = 14.30
   fes[1].cores[3].lanes[3].doRxPolaritySwapped = False
   fes[1].cores[3].lanes[3].doTxPolaritySwapped = False
   fes[1].cores[3].lanes[3].traceLengthToNextEpInInches = 12.12
   fes[1].cores[3].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[3].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[3].lanes[4].traceLengthToNextEpInInches = 14.46
   fes[1].cores[3].lanes[5].doRxPolaritySwapped = False
   fes[1].cores[3].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[3].lanes[5].traceLengthToNextEpInInches = 12.34
   fes[1].cores[3].lanes[6].doRxPolaritySwapped = True
   fes[1].cores[3].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[3].lanes[6].traceLengthToNextEpInInches = 10.42
   fes[1].cores[3].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[3].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[3].lanes[7].traceLengthToNextEpInInches = 8.26
   fes[1].cores[4].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[4].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[4].lanes[0].traceLengthToNextEpInInches = 11.80
   fes[1].cores[4].lanes[1].doRxPolaritySwapped = True
   fes[1].cores[4].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[4].lanes[1].traceLengthToNextEpInInches = 9.72
   fes[1].cores[4].lanes[2].doRxPolaritySwapped = False
   fes[1].cores[4].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[4].lanes[2].traceLengthToNextEpInInches = 7.64
   fes[1].cores[4].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[4].lanes[3].doTxPolaritySwapped = False
   fes[1].cores[4].lanes[3].traceLengthToNextEpInInches = 5.50
   fes[1].cores[4].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[4].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[4].lanes[4].traceLengthToNextEpInInches = 11.79
   fes[1].cores[4].lanes[5].doRxPolaritySwapped = False
   fes[1].cores[4].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[4].lanes[5].traceLengthToNextEpInInches = 9.81
   fes[1].cores[4].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[4].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[4].lanes[6].traceLengthToNextEpInInches = 7.55
   fes[1].cores[4].lanes[7].doRxPolaritySwapped = True
   fes[1].cores[4].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[4].lanes[7].traceLengthToNextEpInInches = 5.32
   fes[1].cores[5].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[5].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[5].lanes[0].traceLengthToNextEpInInches = 11.74
   fes[1].cores[5].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[5].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[5].lanes[1].traceLengthToNextEpInInches = 9.44
   fes[1].cores[5].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[5].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[5].lanes[2].traceLengthToNextEpInInches = 7.43
   fes[1].cores[5].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[5].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[5].lanes[3].traceLengthToNextEpInInches = 5.37
   fes[1].cores[5].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[5].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[5].lanes[4].traceLengthToNextEpInInches = 11.64
   fes[1].cores[5].lanes[5].doRxPolaritySwapped = False
   fes[1].cores[5].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[5].lanes[5].traceLengthToNextEpInInches = 9.65
   fes[1].cores[5].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[5].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[5].lanes[6].traceLengthToNextEpInInches = 7.40
   fes[1].cores[5].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[5].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[5].lanes[7].traceLengthToNextEpInInches = 5.20
   fes[1].cores[6].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[6].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[6].lanes[0].traceLengthToNextEpInInches = 12.60
   fes[1].cores[6].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[6].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[6].lanes[1].traceLengthToNextEpInInches = 10.43
   fes[1].cores[6].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[6].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[6].lanes[2].traceLengthToNextEpInInches = 8.48
   fes[1].cores[6].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[6].lanes[3].doTxPolaritySwapped = False
   fes[1].cores[6].lanes[3].traceLengthToNextEpInInches = 6.28
   fes[1].cores[6].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[6].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[6].lanes[4].traceLengthToNextEpInInches = 12.59
   fes[1].cores[6].lanes[5].doRxPolaritySwapped = False
   fes[1].cores[6].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[6].lanes[5].traceLengthToNextEpInInches = 10.47
   fes[1].cores[6].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[6].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[6].lanes[6].traceLengthToNextEpInInches = 8.36
   fes[1].cores[6].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[6].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[6].lanes[7].traceLengthToNextEpInInches = 6.11
   fes[1].cores[7].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[7].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[7].lanes[0].traceLengthToNextEpInInches = 12.43
   fes[1].cores[7].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[7].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[7].lanes[1].traceLengthToNextEpInInches = 10.28
   fes[1].cores[7].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[7].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[7].lanes[2].traceLengthToNextEpInInches = 8.32
   fes[1].cores[7].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[7].lanes[3].doTxPolaritySwapped = False
   fes[1].cores[7].lanes[3].traceLengthToNextEpInInches = 6.11
   fes[1].cores[7].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[7].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[7].lanes[4].traceLengthToNextEpInInches = 12.43
   fes[1].cores[7].lanes[5].doRxPolaritySwapped = False
   fes[1].cores[7].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[7].lanes[5].traceLengthToNextEpInInches = 10.31
   fes[1].cores[7].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[7].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[7].lanes[6].traceLengthToNextEpInInches = 8.20
   fes[1].cores[7].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[7].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[7].lanes[7].traceLengthToNextEpInInches = 5.95
   fes[1].cores[8].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[8].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[8].lanes[0].traceLengthToNextEpInInches = 11.19
   fes[1].cores[8].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[8].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[8].lanes[1].traceLengthToNextEpInInches = 8.89
   fes[1].cores[8].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[8].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[8].lanes[2].traceLengthToNextEpInInches = 6.87
   fes[1].cores[8].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[8].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[8].lanes[3].traceLengthToNextEpInInches = 4.79
   fes[1].cores[8].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[8].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[8].lanes[4].traceLengthToNextEpInInches = 11.09
   fes[1].cores[8].lanes[5].doRxPolaritySwapped = False
   fes[1].cores[8].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[8].lanes[5].traceLengthToNextEpInInches = 9.10
   fes[1].cores[8].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[8].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[8].lanes[6].traceLengthToNextEpInInches = 6.84
   fes[1].cores[8].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[8].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[8].lanes[7].traceLengthToNextEpInInches = 4.62
   fes[1].cores[9].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[9].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[9].lanes[0].traceLengthToNextEpInInches = 11.04
   fes[1].cores[9].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[9].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[9].lanes[1].traceLengthToNextEpInInches = 8.74
   fes[1].cores[9].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[9].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[9].lanes[2].traceLengthToNextEpInInches = 6.72
   fes[1].cores[9].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[9].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[9].lanes[3].traceLengthToNextEpInInches = 4.63
   fes[1].cores[9].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[9].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[9].lanes[4].traceLengthToNextEpInInches = 10.94
   fes[1].cores[9].lanes[5].doRxPolaritySwapped = False
   fes[1].cores[9].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[9].lanes[5].traceLengthToNextEpInInches = 8.95
   fes[1].cores[9].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[9].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[9].lanes[6].traceLengthToNextEpInInches = 6.69
   fes[1].cores[9].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[9].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[9].lanes[7].traceLengthToNextEpInInches = 4.46
   fes[1].cores[10].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[10].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[10].lanes[0].traceLengthToNextEpInInches = 11.89
   fes[1].cores[10].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[10].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[10].lanes[1].traceLengthToNextEpInInches = 9.73
   fes[1].cores[10].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[10].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[10].lanes[2].traceLengthToNextEpInInches = 7.78
   fes[1].cores[10].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[10].lanes[3].doTxPolaritySwapped = False
   fes[1].cores[10].lanes[3].traceLengthToNextEpInInches = 5.56
   fes[1].cores[10].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[10].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[10].lanes[4].traceLengthToNextEpInInches = 11.89
   fes[1].cores[10].lanes[5].doRxPolaritySwapped = False
   fes[1].cores[10].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[10].lanes[5].traceLengthToNextEpInInches = 9.76
   fes[1].cores[10].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[10].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[10].lanes[6].traceLengthToNextEpInInches = 7.65
   fes[1].cores[10].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[10].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[10].lanes[7].traceLengthToNextEpInInches = 5.39
   fes[1].cores[11].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[11].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[11].lanes[0].traceLengthToNextEpInInches = 11.73
   fes[1].cores[11].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[11].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[11].lanes[1].traceLengthToNextEpInInches = 9.58
   fes[1].cores[11].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[11].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[11].lanes[2].traceLengthToNextEpInInches = 7.61
   fes[1].cores[11].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[11].lanes[3].doTxPolaritySwapped = False
   fes[1].cores[11].lanes[3].traceLengthToNextEpInInches = 5.40
   fes[1].cores[11].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[11].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[11].lanes[4].traceLengthToNextEpInInches = 11.72
   fes[1].cores[11].lanes[5].doRxPolaritySwapped = False
   fes[1].cores[11].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[11].lanes[5].traceLengthToNextEpInInches = 9.61
   fes[1].cores[11].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[11].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[11].lanes[6].traceLengthToNextEpInInches = 7.49
   fes[1].cores[11].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[11].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[11].lanes[7].traceLengthToNextEpInInches = 5.24
   fes[1].cores[12].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[12].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[12].lanes[0].traceLengthToNextEpInInches = 10.51
   fes[1].cores[12].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[12].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[12].lanes[1].traceLengthToNextEpInInches = 8.20
   fes[1].cores[12].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[12].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[12].lanes[2].traceLengthToNextEpInInches = 6.19
   fes[1].cores[12].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[12].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[12].lanes[3].traceLengthToNextEpInInches = 4.13
   fes[1].cores[12].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[12].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[12].lanes[4].traceLengthToNextEpInInches = 10.41
   fes[1].cores[12].lanes[5].doRxPolaritySwapped = False
   fes[1].cores[12].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[12].lanes[5].traceLengthToNextEpInInches = 8.41
   fes[1].cores[12].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[12].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[12].lanes[6].traceLengthToNextEpInInches = 6.16
   fes[1].cores[12].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[12].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[12].lanes[7].traceLengthToNextEpInInches = 3.96
   fes[1].cores[13].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[13].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[13].lanes[0].traceLengthToNextEpInInches = 10.37
   fes[1].cores[13].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[13].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[13].lanes[1].traceLengthToNextEpInInches = 8.06
   fes[1].cores[13].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[13].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[13].lanes[2].traceLengthToNextEpInInches = 6.04
   fes[1].cores[13].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[13].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[13].lanes[3].traceLengthToNextEpInInches = 3.97
   fes[1].cores[13].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[13].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[13].lanes[4].traceLengthToNextEpInInches = 10.26
   fes[1].cores[13].lanes[5].doRxPolaritySwapped = False
   fes[1].cores[13].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[13].lanes[5].traceLengthToNextEpInInches = 8.27
   fes[1].cores[13].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[13].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[13].lanes[6].traceLengthToNextEpInInches = 6.01
   fes[1].cores[13].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[13].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[13].lanes[7].traceLengthToNextEpInInches = 3.80
   fes[1].cores[14].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[14].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[14].lanes[0].traceLengthToNextEpInInches = 11.21
   fes[1].cores[14].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[14].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[14].lanes[1].traceLengthToNextEpInInches = 9.06
   fes[1].cores[14].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[14].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[14].lanes[2].traceLengthToNextEpInInches = 7.10
   fes[1].cores[14].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[14].lanes[3].doTxPolaritySwapped = False
   fes[1].cores[14].lanes[3].traceLengthToNextEpInInches = 4.89
   fes[1].cores[14].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[14].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[14].lanes[4].traceLengthToNextEpInInches = 11.21
   fes[1].cores[14].lanes[5].doRxPolaritySwapped = False
   fes[1].cores[14].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[14].lanes[5].traceLengthToNextEpInInches = 9.09
   fes[1].cores[14].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[14].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[14].lanes[6].traceLengthToNextEpInInches = 6.98
   fes[1].cores[14].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[14].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[14].lanes[7].traceLengthToNextEpInInches = 4.73
   fes[1].cores[15].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[15].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[15].lanes[0].traceLengthToNextEpInInches = 11.05
   fes[1].cores[15].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[15].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[15].lanes[1].traceLengthToNextEpInInches = 8.92
   fes[1].cores[15].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[15].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[15].lanes[2].traceLengthToNextEpInInches = 6.95
   fes[1].cores[15].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[15].lanes[3].doTxPolaritySwapped = False
   fes[1].cores[15].lanes[3].traceLengthToNextEpInInches = 4.75
   fes[1].cores[15].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[15].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[15].lanes[4].traceLengthToNextEpInInches = 11.04
   fes[1].cores[15].lanes[5].doRxPolaritySwapped = False
   fes[1].cores[15].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[15].lanes[5].traceLengthToNextEpInInches = 8.95
   fes[1].cores[15].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[15].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[15].lanes[6].traceLengthToNextEpInInches = 6.84
   fes[1].cores[15].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[15].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[15].lanes[7].traceLengthToNextEpInInches = 4.58
   fes[1].cores[16].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[16].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[16].lanes[0].traceLengthToNextEpInInches = 9.77
   fes[1].cores[16].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[16].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[16].lanes[1].traceLengthToNextEpInInches = 7.72
   fes[1].cores[16].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[16].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[16].lanes[2].traceLengthToNextEpInInches = 5.62
   fes[1].cores[16].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[16].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[16].lanes[3].traceLengthToNextEpInInches = 3.40
   fes[1].cores[16].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[16].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[16].lanes[4].traceLengthToNextEpInInches = 10.06
   fes[1].cores[16].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[16].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[16].lanes[5].traceLengthToNextEpInInches = 7.76
   fes[1].cores[16].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[16].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[16].lanes[6].traceLengthToNextEpInInches = 5.55
   fes[1].cores[16].lanes[7].doRxPolaritySwapped = True
   fes[1].cores[16].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[16].lanes[7].traceLengthToNextEpInInches = 3.51
   fes[1].cores[17].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[17].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[17].lanes[0].traceLengthToNextEpInInches = 9.60
   fes[1].cores[17].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[17].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[17].lanes[1].traceLengthToNextEpInInches = 7.56
   fes[1].cores[17].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[17].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[17].lanes[2].traceLengthToNextEpInInches = 5.45
   fes[1].cores[17].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[17].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[17].lanes[3].traceLengthToNextEpInInches = 3.22
   fes[1].cores[17].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[17].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[17].lanes[4].traceLengthToNextEpInInches = 9.89
   fes[1].cores[17].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[17].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[17].lanes[5].traceLengthToNextEpInInches = 7.59
   fes[1].cores[17].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[17].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[17].lanes[6].traceLengthToNextEpInInches = 5.38
   fes[1].cores[17].lanes[7].doRxPolaritySwapped = True
   fes[1].cores[17].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[17].lanes[7].traceLengthToNextEpInInches = 3.32
   fes[1].cores[18].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[18].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[18].lanes[0].traceLengthToNextEpInInches = 10.55
   fes[1].cores[18].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[18].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[18].lanes[1].traceLengthToNextEpInInches = 8.44
   fes[1].cores[18].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[18].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[18].lanes[2].traceLengthToNextEpInInches = 6.42
   fes[1].cores[18].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[18].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[18].lanes[3].traceLengthToNextEpInInches = 4.16
   fes[1].cores[18].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[18].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[18].lanes[4].traceLengthToNextEpInInches = 10.72
   fes[1].cores[18].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[18].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[18].lanes[5].traceLengthToNextEpInInches = 8.60
   fes[1].cores[18].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[18].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[18].lanes[6].traceLengthToNextEpInInches = 6.39
   fes[1].cores[18].lanes[7].doRxPolaritySwapped = True
   fes[1].cores[18].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[18].lanes[7].traceLengthToNextEpInInches = 4.23
   fes[1].cores[19].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[19].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[19].lanes[0].traceLengthToNextEpInInches = 10.39
   fes[1].cores[19].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[19].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[19].lanes[1].traceLengthToNextEpInInches = 8.31
   fes[1].cores[19].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[19].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[19].lanes[2].traceLengthToNextEpInInches = 6.29
   fes[1].cores[19].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[19].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[19].lanes[3].traceLengthToNextEpInInches = 4.03
   fes[1].cores[19].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[19].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[19].lanes[4].traceLengthToNextEpInInches = 10.55
   fes[1].cores[19].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[19].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[19].lanes[5].traceLengthToNextEpInInches = 8.47
   fes[1].cores[19].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[19].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[19].lanes[6].traceLengthToNextEpInInches = 6.26
   fes[1].cores[19].lanes[7].doRxPolaritySwapped = True
   fes[1].cores[19].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[19].lanes[7].traceLengthToNextEpInInches = 4.09
   fes[1].cores[20].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[20].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[20].lanes[0].traceLengthToNextEpInInches = 9.25
   fes[1].cores[20].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[20].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[20].lanes[1].traceLengthToNextEpInInches = 7.20
   fes[1].cores[20].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[20].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[20].lanes[2].traceLengthToNextEpInInches = 5.10
   fes[1].cores[20].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[20].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[20].lanes[3].traceLengthToNextEpInInches = 2.83
   fes[1].cores[20].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[20].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[20].lanes[4].traceLengthToNextEpInInches = 9.54
   fes[1].cores[20].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[20].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[20].lanes[5].traceLengthToNextEpInInches = 7.24
   fes[1].cores[20].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[20].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[20].lanes[6].traceLengthToNextEpInInches = 5.03
   fes[1].cores[20].lanes[7].doRxPolaritySwapped = True
   fes[1].cores[20].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[20].lanes[7].traceLengthToNextEpInInches = 2.93
   fes[1].cores[21].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[21].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[21].lanes[0].traceLengthToNextEpInInches = 9.12
   fes[1].cores[21].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[21].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[21].lanes[1].traceLengthToNextEpInInches = 7.08
   fes[1].cores[21].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[21].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[21].lanes[2].traceLengthToNextEpInInches = 4.96
   fes[1].cores[21].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[21].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[21].lanes[3].traceLengthToNextEpInInches = 2.67
   fes[1].cores[21].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[21].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[21].lanes[4].traceLengthToNextEpInInches = 9.41
   fes[1].cores[21].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[21].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[21].lanes[5].traceLengthToNextEpInInches = 7.10
   fes[1].cores[21].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[21].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[21].lanes[6].traceLengthToNextEpInInches = 4.90
   fes[1].cores[21].lanes[7].doRxPolaritySwapped = True
   fes[1].cores[21].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[21].lanes[7].traceLengthToNextEpInInches = 2.77
   fes[1].cores[22].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[22].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[22].lanes[0].traceLengthToNextEpInInches = 10.00
   fes[1].cores[22].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[22].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[22].lanes[1].traceLengthToNextEpInInches = 7.85
   fes[1].cores[22].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[22].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[22].lanes[2].traceLengthToNextEpInInches = 5.94
   fes[1].cores[22].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[22].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[22].lanes[3].traceLengthToNextEpInInches = 3.67
   fes[1].cores[22].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[22].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[22].lanes[4].traceLengthToNextEpInInches = 10.16
   fes[1].cores[22].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[22].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[22].lanes[5].traceLengthToNextEpInInches = 8.12
   fes[1].cores[22].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[22].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[22].lanes[6].traceLengthToNextEpInInches = 5.80
   fes[1].cores[22].lanes[7].doRxPolaritySwapped = True
   fes[1].cores[22].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[22].lanes[7].traceLengthToNextEpInInches = 3.63
   fes[1].cores[23].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[23].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[23].lanes[0].traceLengthToNextEpInInches = 9.85
   fes[1].cores[23].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[23].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[23].lanes[1].traceLengthToNextEpInInches = 7.72
   fes[1].cores[23].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[23].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[23].lanes[2].traceLengthToNextEpInInches = 5.70
   fes[1].cores[23].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[23].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[23].lanes[3].traceLengthToNextEpInInches = 3.42
   fes[1].cores[23].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[23].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[23].lanes[4].traceLengthToNextEpInInches = 10.01
   fes[1].cores[23].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[23].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[23].lanes[5].traceLengthToNextEpInInches = 7.87
   fes[1].cores[23].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[23].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[23].lanes[6].traceLengthToNextEpInInches = 5.67
   fes[1].cores[23].lanes[7].doRxPolaritySwapped = True
   fes[1].cores[23].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[23].lanes[7].traceLengthToNextEpInInches = 3.49
   fes[1].cores[24].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[24].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[24].lanes[0].traceLengthToNextEpInInches = 8.73
   fes[1].cores[24].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[24].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[24].lanes[1].traceLengthToNextEpInInches = 6.69
   fes[1].cores[24].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[24].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[24].lanes[2].traceLengthToNextEpInInches = 4.58
   fes[1].cores[24].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[24].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[24].lanes[3].traceLengthToNextEpInInches = 2.45
   fes[1].cores[24].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[24].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[24].lanes[4].traceLengthToNextEpInInches = 9.03
   fes[1].cores[24].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[24].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[24].lanes[5].traceLengthToNextEpInInches = 6.73
   fes[1].cores[24].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[24].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[24].lanes[6].traceLengthToNextEpInInches = 4.51
   fes[1].cores[24].lanes[7].doRxPolaritySwapped = True
   fes[1].cores[24].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[24].lanes[7].traceLengthToNextEpInInches = 2.56
   fes[1].cores[25].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[25].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[25].lanes[0].traceLengthToNextEpInInches = 8.61
   fes[1].cores[25].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[25].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[25].lanes[1].traceLengthToNextEpInInches = 6.56
   fes[1].cores[25].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[25].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[25].lanes[2].traceLengthToNextEpInInches = 4.45
   fes[1].cores[25].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[25].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[25].lanes[3].traceLengthToNextEpInInches = 2.30
   fes[1].cores[25].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[25].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[25].lanes[4].traceLengthToNextEpInInches = 8.90
   fes[1].cores[25].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[25].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[25].lanes[5].traceLengthToNextEpInInches = 6.59
   fes[1].cores[25].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[25].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[25].lanes[6].traceLengthToNextEpInInches = 4.38
   fes[1].cores[25].lanes[7].doRxPolaritySwapped = True
   fes[1].cores[25].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[25].lanes[7].traceLengthToNextEpInInches = 2.40
   fes[1].cores[26].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[26].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[26].lanes[0].traceLengthToNextEpInInches = 9.64
   fes[1].cores[26].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[26].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[26].lanes[1].traceLengthToNextEpInInches = 7.44
   fes[1].cores[26].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[26].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[26].lanes[2].traceLengthToNextEpInInches = 5.42
   fes[1].cores[26].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[26].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[26].lanes[3].traceLengthToNextEpInInches = 3.15
   fes[1].cores[26].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[26].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[26].lanes[4].traceLengthToNextEpInInches = 9.79
   fes[1].cores[26].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[26].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[26].lanes[5].traceLengthToNextEpInInches = 7.60
   fes[1].cores[26].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[26].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[26].lanes[6].traceLengthToNextEpInInches = 5.39
   fes[1].cores[26].lanes[7].doRxPolaritySwapped = True
   fes[1].cores[26].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[26].lanes[7].traceLengthToNextEpInInches = 3.21
   fes[1].cores[27].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[27].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[27].lanes[0].traceLengthToNextEpInInches = 9.37
   fes[1].cores[27].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[27].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[27].lanes[1].traceLengthToNextEpInInches = 7.15
   fes[1].cores[27].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[27].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[27].lanes[2].traceLengthToNextEpInInches = 5.18
   fes[1].cores[27].lanes[3].doRxPolaritySwapped = False
   fes[1].cores[27].lanes[3].doTxPolaritySwapped = False
   fes[1].cores[27].lanes[3].traceLengthToNextEpInInches = 3.13
   fes[1].cores[27].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[27].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[27].lanes[4].traceLengthToNextEpInInches = 9.40
   fes[1].cores[27].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[27].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[27].lanes[5].traceLengthToNextEpInInches = 7.26
   fes[1].cores[27].lanes[6].doRxPolaritySwapped = True
   fes[1].cores[27].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[27].lanes[6].traceLengthToNextEpInInches = 5.25
   fes[1].cores[27].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[27].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[27].lanes[7].traceLengthToNextEpInInches = 3.10
   fes[1].cores[28].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[28].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[28].lanes[0].traceLengthToNextEpInInches = 8.26
   fes[1].cores[28].lanes[1].doRxPolaritySwapped = True
   fes[1].cores[28].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[28].lanes[1].traceLengthToNextEpInInches = 6.13
   fes[1].cores[28].lanes[2].doRxPolaritySwapped = False
   fes[1].cores[28].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[28].lanes[2].traceLengthToNextEpInInches = 4.03
   fes[1].cores[28].lanes[3].doRxPolaritySwapped = False
   fes[1].cores[28].lanes[3].doTxPolaritySwapped = False
   fes[1].cores[28].lanes[3].traceLengthToNextEpInInches = 1.88
   fes[1].cores[28].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[28].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[28].lanes[4].traceLengthToNextEpInInches = 4.02
   fes[1].cores[28].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[28].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[28].lanes[5].traceLengthToNextEpInInches = 1.87
   fes[1].cores[28].lanes[6].doRxPolaritySwapped = True
   fes[1].cores[28].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[28].lanes[6].traceLengthToNextEpInInches = 8.25
   fes[1].cores[28].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[28].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[28].lanes[7].traceLengthToNextEpInInches = 6.13
   fes[1].cores[29].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[29].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[29].lanes[0].traceLengthToNextEpInInches = 8.26
   fes[1].cores[29].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[29].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[29].lanes[1].traceLengthToNextEpInInches = 6.12
   fes[1].cores[29].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[29].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[29].lanes[2].traceLengthToNextEpInInches = 4.00
   fes[1].cores[29].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[29].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[29].lanes[3].traceLengthToNextEpInInches = 1.87
   fes[1].cores[29].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[29].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[29].lanes[4].traceLengthToNextEpInInches = 3.99
   fes[1].cores[29].lanes[5].doRxPolaritySwapped = False
   fes[1].cores[29].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[29].lanes[5].traceLengthToNextEpInInches = 1.87
   fes[1].cores[29].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[29].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[29].lanes[6].traceLengthToNextEpInInches = 8.27
   fes[1].cores[29].lanes[7].doRxPolaritySwapped = True
   fes[1].cores[29].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[29].lanes[7].traceLengthToNextEpInInches = 6.13
   fes[1].cores[30].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[30].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[30].lanes[0].traceLengthToNextEpInInches = 9.42
   fes[1].cores[30].lanes[1].doRxPolaritySwapped = True
   fes[1].cores[30].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[30].lanes[1].traceLengthToNextEpInInches = 7.15
   fes[1].cores[30].lanes[2].doRxPolaritySwapped = False
   fes[1].cores[30].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[30].lanes[2].traceLengthToNextEpInInches = 5.13
   fes[1].cores[30].lanes[3].doRxPolaritySwapped = False
   fes[1].cores[30].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[30].lanes[3].traceLengthToNextEpInInches = 2.88
   fes[1].cores[30].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[30].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[30].lanes[4].traceLengthToNextEpInInches = 5.14
   fes[1].cores[30].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[30].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[30].lanes[5].traceLengthToNextEpInInches = 2.88
   fes[1].cores[30].lanes[6].doRxPolaritySwapped = True
   fes[1].cores[30].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[30].lanes[6].traceLengthToNextEpInInches = 9.42
   fes[1].cores[30].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[30].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[30].lanes[7].traceLengthToNextEpInInches = 7.15
   fes[1].cores[31].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[31].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[31].lanes[0].traceLengthToNextEpInInches = 9.41
   fes[1].cores[31].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[31].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[31].lanes[1].traceLengthToNextEpInInches = 7.14
   fes[1].cores[31].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[31].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[31].lanes[2].traceLengthToNextEpInInches = 5.12
   fes[1].cores[31].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[31].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[31].lanes[3].traceLengthToNextEpInInches = 2.89
   fes[1].cores[31].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[31].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[31].lanes[4].traceLengthToNextEpInInches = 5.12
   fes[1].cores[31].lanes[5].doRxPolaritySwapped = False
   fes[1].cores[31].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[31].lanes[5].traceLengthToNextEpInInches = 2.90
   fes[1].cores[31].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[31].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[31].lanes[6].traceLengthToNextEpInInches = 9.41
   fes[1].cores[31].lanes[7].doRxPolaritySwapped = True
   fes[1].cores[31].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[31].lanes[7].traceLengthToNextEpInInches = 7.14
   fes[1].cores[32].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[32].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[32].lanes[0].traceLengthToNextEpInInches = 4.00
   fes[1].cores[32].lanes[1].doRxPolaritySwapped = True
   fes[1].cores[32].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[32].lanes[1].traceLengthToNextEpInInches = 1.90
   fes[1].cores[32].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[32].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[32].lanes[2].traceLengthToNextEpInInches = 8.26
   fes[1].cores[32].lanes[3].doRxPolaritySwapped = False
   fes[1].cores[32].lanes[3].doTxPolaritySwapped = False
   fes[1].cores[32].lanes[3].traceLengthToNextEpInInches = 6.14
   fes[1].cores[32].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[32].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[32].lanes[4].traceLengthToNextEpInInches = 8.27
   fes[1].cores[32].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[32].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[32].lanes[5].traceLengthToNextEpInInches = 6.15
   fes[1].cores[32].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[32].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[32].lanes[6].traceLengthToNextEpInInches = 4.00
   fes[1].cores[32].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[32].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[32].lanes[7].traceLengthToNextEpInInches = 1.89
   fes[1].cores[33].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[33].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[33].lanes[0].traceLengthToNextEpInInches = 4.04
   fes[1].cores[33].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[33].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[33].lanes[1].traceLengthToNextEpInInches = 1.92
   fes[1].cores[33].lanes[2].doRxPolaritySwapped = False
   fes[1].cores[33].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[33].lanes[2].traceLengthToNextEpInInches = 8.25
   fes[1].cores[33].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[33].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[33].lanes[3].traceLengthToNextEpInInches = 6.14
   fes[1].cores[33].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[33].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[33].lanes[4].traceLengthToNextEpInInches = 8.25
   fes[1].cores[33].lanes[5].doRxPolaritySwapped = False
   fes[1].cores[33].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[33].lanes[5].traceLengthToNextEpInInches = 6.14
   fes[1].cores[33].lanes[6].doRxPolaritySwapped = True
   fes[1].cores[33].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[33].lanes[6].traceLengthToNextEpInInches = 4.03
   fes[1].cores[33].lanes[7].doRxPolaritySwapped = True
   fes[1].cores[33].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[33].lanes[7].traceLengthToNextEpInInches = 1.91
   fes[1].cores[34].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[34].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[34].lanes[0].traceLengthToNextEpInInches = 5.12
   fes[1].cores[34].lanes[1].doRxPolaritySwapped = True
   fes[1].cores[34].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[34].lanes[1].traceLengthToNextEpInInches = 2.90
   fes[1].cores[34].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[34].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[34].lanes[2].traceLengthToNextEpInInches = 9.39
   fes[1].cores[34].lanes[3].doRxPolaritySwapped = False
   fes[1].cores[34].lanes[3].doTxPolaritySwapped = False
   fes[1].cores[34].lanes[3].traceLengthToNextEpInInches = 7.14
   fes[1].cores[34].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[34].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[34].lanes[4].traceLengthToNextEpInInches = 9.40
   fes[1].cores[34].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[34].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[34].lanes[5].traceLengthToNextEpInInches = 7.13
   fes[1].cores[34].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[34].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[34].lanes[6].traceLengthToNextEpInInches = 5.13
   fes[1].cores[34].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[34].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[34].lanes[7].traceLengthToNextEpInInches = 2.91
   fes[1].cores[35].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[35].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[35].lanes[0].traceLengthToNextEpInInches = 5.16
   fes[1].cores[35].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[35].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[35].lanes[1].traceLengthToNextEpInInches = 2.90
   fes[1].cores[35].lanes[2].doRxPolaritySwapped = False
   fes[1].cores[35].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[35].lanes[2].traceLengthToNextEpInInches = 9.41
   fes[1].cores[35].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[35].lanes[3].doTxPolaritySwapped = False
   fes[1].cores[35].lanes[3].traceLengthToNextEpInInches = 7.15
   fes[1].cores[35].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[35].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[35].lanes[4].traceLengthToNextEpInInches = 9.40
   fes[1].cores[35].lanes[5].doRxPolaritySwapped = False
   fes[1].cores[35].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[35].lanes[5].traceLengthToNextEpInInches = 7.14
   fes[1].cores[35].lanes[6].doRxPolaritySwapped = True
   fes[1].cores[35].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[35].lanes[6].traceLengthToNextEpInInches = 5.15
   fes[1].cores[35].lanes[7].doRxPolaritySwapped = True
   fes[1].cores[35].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[35].lanes[7].traceLengthToNextEpInInches = 2.90
   fes[1].cores[36].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[36].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[36].lanes[0].traceLengthToNextEpInInches = 8.36
   fes[1].cores[36].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[36].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[36].lanes[1].traceLengthToNextEpInInches = 6.28
   fes[1].cores[36].lanes[2].doRxPolaritySwapped = False
   fes[1].cores[36].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[36].lanes[2].traceLengthToNextEpInInches = 4.23
   fes[1].cores[36].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[36].lanes[3].doTxPolaritySwapped = False
   fes[1].cores[36].lanes[3].traceLengthToNextEpInInches = 1.91
   fes[1].cores[36].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[36].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[36].lanes[4].traceLengthToNextEpInInches = 8.27
   fes[1].cores[36].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[36].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[36].lanes[5].traceLengthToNextEpInInches = 6.18
   fes[1].cores[36].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[36].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[36].lanes[6].traceLengthToNextEpInInches = 4.07
   fes[1].cores[36].lanes[7].doRxPolaritySwapped = True
   fes[1].cores[36].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[36].lanes[7].traceLengthToNextEpInInches = 1.94
   fes[1].cores[37].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[37].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[37].lanes[0].traceLengthToNextEpInInches = 8.78
   fes[1].cores[37].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[37].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[37].lanes[1].traceLengthToNextEpInInches = 6.47
   fes[1].cores[37].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[37].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[37].lanes[2].traceLengthToNextEpInInches = 4.27
   fes[1].cores[37].lanes[3].doRxPolaritySwapped = False
   fes[1].cores[37].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[37].lanes[3].traceLengthToNextEpInInches = 2.29
   fes[1].cores[37].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[37].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[37].lanes[4].traceLengthToNextEpInInches = 8.48
   fes[1].cores[37].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[37].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[37].lanes[5].traceLengthToNextEpInInches = 6.45
   fes[1].cores[37].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[37].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[37].lanes[6].traceLengthToNextEpInInches = 4.34
   fes[1].cores[37].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[37].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[37].lanes[7].traceLengthToNextEpInInches = 2.19
   fes[1].cores[38].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[38].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[38].lanes[0].traceLengthToNextEpInInches = 9.94
   fes[1].cores[38].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[38].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[38].lanes[1].traceLengthToNextEpInInches = 7.76
   fes[1].cores[38].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[38].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[38].lanes[2].traceLengthToNextEpInInches = 5.56
   fes[1].cores[38].lanes[3].doRxPolaritySwapped = False
   fes[1].cores[38].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[38].lanes[3].traceLengthToNextEpInInches = 3.39
   fes[1].cores[38].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[38].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[38].lanes[4].traceLengthToNextEpInInches = 9.78
   fes[1].cores[38].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[38].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[38].lanes[5].traceLengthToNextEpInInches = 7.60
   fes[1].cores[38].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[38].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[38].lanes[6].traceLengthToNextEpInInches = 5.58
   fes[1].cores[38].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[38].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[38].lanes[7].traceLengthToNextEpInInches = 3.32
   fes[1].cores[39].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[39].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[39].lanes[0].traceLengthToNextEpInInches = 10.10
   fes[1].cores[39].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[39].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[39].lanes[1].traceLengthToNextEpInInches = 7.90
   fes[1].cores[39].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[39].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[39].lanes[2].traceLengthToNextEpInInches = 5.70
   fes[1].cores[39].lanes[3].doRxPolaritySwapped = False
   fes[1].cores[39].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[39].lanes[3].traceLengthToNextEpInInches = 3.53
   fes[1].cores[39].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[39].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[39].lanes[4].traceLengthToNextEpInInches = 9.93
   fes[1].cores[39].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[39].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[39].lanes[5].traceLengthToNextEpInInches = 7.74
   fes[1].cores[39].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[39].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[39].lanes[6].traceLengthToNextEpInInches = 5.72
   fes[1].cores[39].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[39].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[39].lanes[7].traceLengthToNextEpInInches = 3.47
   fes[1].cores[40].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[40].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[40].lanes[0].traceLengthToNextEpInInches = 9.05
   fes[1].cores[40].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[40].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[40].lanes[1].traceLengthToNextEpInInches = 6.75
   fes[1].cores[40].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[40].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[40].lanes[2].traceLengthToNextEpInInches = 4.57
   fes[1].cores[40].lanes[3].doRxPolaritySwapped = False
   fes[1].cores[40].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[40].lanes[3].traceLengthToNextEpInInches = 2.50
   fes[1].cores[40].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[40].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[40].lanes[4].traceLengthToNextEpInInches = 8.76
   fes[1].cores[40].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[40].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[40].lanes[5].traceLengthToNextEpInInches = 6.72
   fes[1].cores[40].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[40].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[40].lanes[6].traceLengthToNextEpInInches = 4.64
   fes[1].cores[40].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[40].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[40].lanes[7].traceLengthToNextEpInInches = 2.39
   fes[1].cores[41].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[41].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[41].lanes[0].traceLengthToNextEpInInches = 9.29
   fes[1].cores[41].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[41].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[41].lanes[1].traceLengthToNextEpInInches = 6.98
   fes[1].cores[41].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[41].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[41].lanes[2].traceLengthToNextEpInInches = 4.70
   fes[1].cores[41].lanes[3].doRxPolaritySwapped = False
   fes[1].cores[41].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[41].lanes[3].traceLengthToNextEpInInches = 2.65
   fes[1].cores[41].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[41].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[41].lanes[4].traceLengthToNextEpInInches = 8.90
   fes[1].cores[41].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[41].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[41].lanes[5].traceLengthToNextEpInInches = 6.86
   fes[1].cores[41].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[41].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[41].lanes[6].traceLengthToNextEpInInches = 4.87
   fes[1].cores[41].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[41].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[41].lanes[7].traceLengthToNextEpInInches = 2.55
   fes[1].cores[42].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[42].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[42].lanes[0].traceLengthToNextEpInInches = 10.31
   fes[1].cores[42].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[42].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[42].lanes[1].traceLengthToNextEpInInches = 8.27
   fes[1].cores[42].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[42].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[42].lanes[2].traceLengthToNextEpInInches = 6.08
   fes[1].cores[42].lanes[3].doRxPolaritySwapped = False
   fes[1].cores[42].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[42].lanes[3].traceLengthToNextEpInInches = 3.91
   fes[1].cores[42].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[42].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[42].lanes[4].traceLengthToNextEpInInches = 10.15
   fes[1].cores[42].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[42].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[42].lanes[5].traceLengthToNextEpInInches = 8.11
   fes[1].cores[42].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[42].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[42].lanes[6].traceLengthToNextEpInInches = 6.11
   fes[1].cores[42].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[42].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[42].lanes[7].traceLengthToNextEpInInches = 3.85
   fes[1].cores[43].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[43].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[43].lanes[0].traceLengthToNextEpInInches = 10.53
   fes[1].cores[43].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[43].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[43].lanes[1].traceLengthToNextEpInInches = 8.40
   fes[1].cores[43].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[43].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[43].lanes[2].traceLengthToNextEpInInches = 6.22
   fes[1].cores[43].lanes[3].doRxPolaritySwapped = False
   fes[1].cores[43].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[43].lanes[3].traceLengthToNextEpInInches = 4.05
   fes[1].cores[43].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[43].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[43].lanes[4].traceLengthToNextEpInInches = 10.30
   fes[1].cores[43].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[43].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[43].lanes[5].traceLengthToNextEpInInches = 8.25
   fes[1].cores[43].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[43].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[43].lanes[6].traceLengthToNextEpInInches = 6.24
   fes[1].cores[43].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[43].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[43].lanes[7].traceLengthToNextEpInInches = 3.99
   fes[1].cores[44].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[44].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[44].lanes[0].traceLengthToNextEpInInches = 9.61
   fes[1].cores[44].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[44].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[44].lanes[1].traceLengthToNextEpInInches = 7.31
   fes[1].cores[44].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[44].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[44].lanes[2].traceLengthToNextEpInInches = 5.13
   fes[1].cores[44].lanes[3].doRxPolaritySwapped = False
   fes[1].cores[44].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[44].lanes[3].traceLengthToNextEpInInches = 3.07
   fes[1].cores[44].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[44].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[44].lanes[4].traceLengthToNextEpInInches = 9.32
   fes[1].cores[44].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[44].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[44].lanes[5].traceLengthToNextEpInInches = 7.29
   fes[1].cores[44].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[44].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[44].lanes[6].traceLengthToNextEpInInches = 5.19
   fes[1].cores[44].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[44].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[44].lanes[7].traceLengthToNextEpInInches = 2.97
   fes[1].cores[45].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[45].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[45].lanes[0].traceLengthToNextEpInInches = 9.75
   fes[1].cores[45].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[45].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[45].lanes[1].traceLengthToNextEpInInches = 7.45
   fes[1].cores[45].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[45].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[45].lanes[2].traceLengthToNextEpInInches = 5.26
   fes[1].cores[45].lanes[3].doRxPolaritySwapped = False
   fes[1].cores[45].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[45].lanes[3].traceLengthToNextEpInInches = 3.23
   fes[1].cores[45].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[45].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[45].lanes[4].traceLengthToNextEpInInches = 9.46
   fes[1].cores[45].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[45].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[45].lanes[5].traceLengthToNextEpInInches = 7.43
   fes[1].cores[45].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[45].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[45].lanes[6].traceLengthToNextEpInInches = 5.33
   fes[1].cores[45].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[45].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[45].lanes[7].traceLengthToNextEpInInches = 3.14
   fes[1].cores[46].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[46].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[46].lanes[0].traceLengthToNextEpInInches = 10.85
   fes[1].cores[46].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[46].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[46].lanes[1].traceLengthToNextEpInInches = 8.74
   fes[1].cores[46].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[46].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[46].lanes[2].traceLengthToNextEpInInches = 6.56
   fes[1].cores[46].lanes[3].doRxPolaritySwapped = False
   fes[1].cores[46].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[46].lanes[3].traceLengthToNextEpInInches = 4.38
   fes[1].cores[46].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[46].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[46].lanes[4].traceLengthToNextEpInInches = 10.69
   fes[1].cores[46].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[46].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[46].lanes[5].traceLengthToNextEpInInches = 8.59
   fes[1].cores[46].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[46].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[46].lanes[6].traceLengthToNextEpInInches = 6.58
   fes[1].cores[46].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[46].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[46].lanes[7].traceLengthToNextEpInInches = 4.32
   fes[1].cores[47].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[47].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[47].lanes[0].traceLengthToNextEpInInches = 11.04
   fes[1].cores[47].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[47].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[47].lanes[1].traceLengthToNextEpInInches = 8.91
   fes[1].cores[47].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[47].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[47].lanes[2].traceLengthToNextEpInInches = 6.72
   fes[1].cores[47].lanes[3].doRxPolaritySwapped = False
   fes[1].cores[47].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[47].lanes[3].traceLengthToNextEpInInches = 4.54
   fes[1].cores[47].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[47].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[47].lanes[4].traceLengthToNextEpInInches = 10.87
   fes[1].cores[47].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[47].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[47].lanes[5].traceLengthToNextEpInInches = 8.75
   fes[1].cores[47].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[47].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[47].lanes[6].traceLengthToNextEpInInches = 6.74
   fes[1].cores[47].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[47].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[47].lanes[7].traceLengthToNextEpInInches = 4.49
   fes[1].cores[48].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[48].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[48].lanes[0].traceLengthToNextEpInInches = 9.96
   fes[1].cores[48].lanes[1].doRxPolaritySwapped = True
   fes[1].cores[48].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[48].lanes[1].traceLengthToNextEpInInches = 7.97
   fes[1].cores[48].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[48].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[48].lanes[2].traceLengthToNextEpInInches = 5.73
   fes[1].cores[48].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[48].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[48].lanes[3].traceLengthToNextEpInInches = 3.54
   fes[1].cores[48].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[48].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[48].lanes[4].traceLengthToNextEpInInches = 10.07
   fes[1].cores[48].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[48].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[48].lanes[5].traceLengthToNextEpInInches = 7.77
   fes[1].cores[48].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[48].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[48].lanes[6].traceLengthToNextEpInInches = 5.76
   fes[1].cores[48].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[48].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[48].lanes[7].traceLengthToNextEpInInches = 3.71
   fes[1].cores[49].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[49].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[49].lanes[0].traceLengthToNextEpInInches = 10.11
   fes[1].cores[49].lanes[1].doRxPolaritySwapped = True
   fes[1].cores[49].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[49].lanes[1].traceLengthToNextEpInInches = 8.11
   fes[1].cores[49].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[49].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[49].lanes[2].traceLengthToNextEpInInches = 5.87
   fes[1].cores[49].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[49].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[49].lanes[3].traceLengthToNextEpInInches = 3.70
   fes[1].cores[49].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[49].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[49].lanes[4].traceLengthToNextEpInInches = 10.21
   fes[1].cores[49].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[49].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[49].lanes[5].traceLengthToNextEpInInches = 7.91
   fes[1].cores[49].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[49].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[49].lanes[6].traceLengthToNextEpInInches = 5.91
   fes[1].cores[49].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[49].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[49].lanes[7].traceLengthToNextEpInInches = 3.87
   fes[1].cores[50].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[50].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[50].lanes[0].traceLengthToNextEpInInches = 11.32
   fes[1].cores[50].lanes[1].doRxPolaritySwapped = True
   fes[1].cores[50].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[50].lanes[1].traceLengthToNextEpInInches = 9.23
   fes[1].cores[50].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[50].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[50].lanes[2].traceLengthToNextEpInInches = 7.13
   fes[1].cores[50].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[50].lanes[3].doTxPolaritySwapped = False
   fes[1].cores[50].lanes[3].traceLengthToNextEpInInches = 4.85
   fes[1].cores[50].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[50].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[50].lanes[4].traceLengthToNextEpInInches = 11.34
   fes[1].cores[50].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[50].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[50].lanes[5].traceLengthToNextEpInInches = 9.21
   fes[1].cores[50].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[50].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[50].lanes[6].traceLengthToNextEpInInches = 7.25
   fes[1].cores[50].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[50].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[50].lanes[7].traceLengthToNextEpInInches = 5.01
   fes[1].cores[51].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[51].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[51].lanes[0].traceLengthToNextEpInInches = 11.49
   fes[1].cores[51].lanes[1].doRxPolaritySwapped = True
   fes[1].cores[51].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[51].lanes[1].traceLengthToNextEpInInches = 9.38
   fes[1].cores[51].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[51].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[51].lanes[2].traceLengthToNextEpInInches = 7.27
   fes[1].cores[51].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[51].lanes[3].doTxPolaritySwapped = False
   fes[1].cores[51].lanes[3].traceLengthToNextEpInInches = 4.99
   fes[1].cores[51].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[51].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[51].lanes[4].traceLengthToNextEpInInches = 11.50
   fes[1].cores[51].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[51].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[51].lanes[5].traceLengthToNextEpInInches = 9.35
   fes[1].cores[51].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[51].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[51].lanes[6].traceLengthToNextEpInInches = 7.39
   fes[1].cores[51].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[51].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[51].lanes[7].traceLengthToNextEpInInches = 5.15
   fes[1].cores[52].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[52].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[52].lanes[0].traceLengthToNextEpInInches = 10.61
   fes[1].cores[52].lanes[1].doRxPolaritySwapped = True
   fes[1].cores[52].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[52].lanes[1].traceLengthToNextEpInInches = 8.61
   fes[1].cores[52].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[52].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[52].lanes[2].traceLengthToNextEpInInches = 6.37
   fes[1].cores[52].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[52].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[52].lanes[3].traceLengthToNextEpInInches = 4.20
   fes[1].cores[52].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[52].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[52].lanes[4].traceLengthToNextEpInInches = 10.71
   fes[1].cores[52].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[52].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[52].lanes[5].traceLengthToNextEpInInches = 8.41
   fes[1].cores[52].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[52].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[52].lanes[6].traceLengthToNextEpInInches = 6.41
   fes[1].cores[52].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[52].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[52].lanes[7].traceLengthToNextEpInInches = 4.37
   fes[1].cores[53].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[53].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[53].lanes[0].traceLengthToNextEpInInches = 10.76
   fes[1].cores[53].lanes[1].doRxPolaritySwapped = True
   fes[1].cores[53].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[53].lanes[1].traceLengthToNextEpInInches = 8.77
   fes[1].cores[53].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[53].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[53].lanes[2].traceLengthToNextEpInInches = 6.53
   fes[1].cores[53].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[53].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[53].lanes[3].traceLengthToNextEpInInches = 4.36
   fes[1].cores[53].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[53].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[53].lanes[4].traceLengthToNextEpInInches = 10.86
   fes[1].cores[53].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[53].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[53].lanes[5].traceLengthToNextEpInInches = 8.56
   fes[1].cores[53].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[53].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[53].lanes[6].traceLengthToNextEpInInches = 6.57
   fes[1].cores[53].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[53].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[53].lanes[7].traceLengthToNextEpInInches = 4.54
   fes[1].cores[54].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[54].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[54].lanes[0].traceLengthToNextEpInInches = 12.01
   fes[1].cores[54].lanes[1].doRxPolaritySwapped = True
   fes[1].cores[54].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[54].lanes[1].traceLengthToNextEpInInches = 9.90
   fes[1].cores[54].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[54].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[54].lanes[2].traceLengthToNextEpInInches = 7.80
   fes[1].cores[54].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[54].lanes[3].doTxPolaritySwapped = False
   fes[1].cores[54].lanes[3].traceLengthToNextEpInInches = 5.53
   fes[1].cores[54].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[54].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[54].lanes[4].traceLengthToNextEpInInches = 12.02
   fes[1].cores[54].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[54].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[54].lanes[5].traceLengthToNextEpInInches = 9.87
   fes[1].cores[54].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[54].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[54].lanes[6].traceLengthToNextEpInInches = 7.93
   fes[1].cores[54].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[54].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[54].lanes[7].traceLengthToNextEpInInches = 5.70
   fes[1].cores[55].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[55].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[55].lanes[0].traceLengthToNextEpInInches = 12.18
   fes[1].cores[55].lanes[1].doRxPolaritySwapped = True
   fes[1].cores[55].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[55].lanes[1].traceLengthToNextEpInInches = 10.06
   fes[1].cores[55].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[55].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[55].lanes[2].traceLengthToNextEpInInches = 7.96
   fes[1].cores[55].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[55].lanes[3].doTxPolaritySwapped = False
   fes[1].cores[55].lanes[3].traceLengthToNextEpInInches = 5.69
   fes[1].cores[55].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[55].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[55].lanes[4].traceLengthToNextEpInInches = 12.19
   fes[1].cores[55].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[55].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[55].lanes[5].traceLengthToNextEpInInches = 10.02
   fes[1].cores[55].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[55].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[55].lanes[6].traceLengthToNextEpInInches = 8.09
   fes[1].cores[55].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[55].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[55].lanes[7].traceLengthToNextEpInInches = 5.86
   fes[1].cores[56].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[56].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[56].lanes[0].traceLengthToNextEpInInches = 11.32
   fes[1].cores[56].lanes[1].doRxPolaritySwapped = True
   fes[1].cores[56].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[56].lanes[1].traceLengthToNextEpInInches = 9.33
   fes[1].cores[56].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[56].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[56].lanes[2].traceLengthToNextEpInInches = 7.10
   fes[1].cores[56].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[56].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[56].lanes[3].traceLengthToNextEpInInches = 4.95
   fes[1].cores[56].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[56].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[56].lanes[4].traceLengthToNextEpInInches = 11.42
   fes[1].cores[56].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[56].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[56].lanes[5].traceLengthToNextEpInInches = 9.12
   fes[1].cores[56].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[56].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[56].lanes[6].traceLengthToNextEpInInches = 7.14
   fes[1].cores[56].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[56].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[56].lanes[7].traceLengthToNextEpInInches = 5.12
   fes[1].cores[57].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[57].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[57].lanes[0].traceLengthToNextEpInInches = 11.48
   fes[1].cores[57].lanes[1].doRxPolaritySwapped = True
   fes[1].cores[57].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[57].lanes[1].traceLengthToNextEpInInches = 9.49
   fes[1].cores[57].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[57].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[57].lanes[2].traceLengthToNextEpInInches = 7.25
   fes[1].cores[57].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[57].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[57].lanes[3].traceLengthToNextEpInInches = 5.11
   fes[1].cores[57].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[57].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[57].lanes[4].traceLengthToNextEpInInches = 11.58
   fes[1].cores[57].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[57].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[57].lanes[5].traceLengthToNextEpInInches = 9.28
   fes[1].cores[57].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[57].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[57].lanes[6].traceLengthToNextEpInInches = 7.29
   fes[1].cores[57].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[57].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[57].lanes[7].traceLengthToNextEpInInches = 5.28
   fes[1].cores[58].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[58].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[58].lanes[0].traceLengthToNextEpInInches = 12.71
   fes[1].cores[58].lanes[1].doRxPolaritySwapped = True
   fes[1].cores[58].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[58].lanes[1].traceLengthToNextEpInInches = 10.62
   fes[1].cores[58].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[58].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[58].lanes[2].traceLengthToNextEpInInches = 8.52
   fes[1].cores[58].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[58].lanes[3].doTxPolaritySwapped = False
   fes[1].cores[58].lanes[3].traceLengthToNextEpInInches = 6.26
   fes[1].cores[58].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[58].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[58].lanes[4].traceLengthToNextEpInInches = 12.72
   fes[1].cores[58].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[58].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[58].lanes[5].traceLengthToNextEpInInches = 10.59
   fes[1].cores[58].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[58].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[58].lanes[6].traceLengthToNextEpInInches = 8.65
   fes[1].cores[58].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[58].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[58].lanes[7].traceLengthToNextEpInInches = 6.42
   fes[1].cores[59].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[59].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[59].lanes[0].traceLengthToNextEpInInches = 12.92
   fes[1].cores[59].lanes[1].doRxPolaritySwapped = True
   fes[1].cores[59].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[59].lanes[1].traceLengthToNextEpInInches = 10.83
   fes[1].cores[59].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[59].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[59].lanes[2].traceLengthToNextEpInInches = 8.55
   fes[1].cores[59].lanes[3].doRxPolaritySwapped = False
   fes[1].cores[59].lanes[3].doTxPolaritySwapped = False
   fes[1].cores[59].lanes[3].traceLengthToNextEpInInches = 6.59
   fes[1].cores[59].lanes[4].doRxPolaritySwapped = True
   fes[1].cores[59].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[59].lanes[4].traceLengthToNextEpInInches = 12.75
   fes[1].cores[59].lanes[5].doRxPolaritySwapped = False
   fes[1].cores[59].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[59].lanes[5].traceLengthToNextEpInInches = 10.83
   fes[1].cores[59].lanes[6].doRxPolaritySwapped = True
   fes[1].cores[59].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[59].lanes[6].traceLengthToNextEpInInches = 8.63
   fes[1].cores[59].lanes[7].doRxPolaritySwapped = False
   fes[1].cores[59].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[59].lanes[7].traceLengthToNextEpInInches = 6.68
   fes[1].cores[60].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[60].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[60].lanes[0].traceLengthToNextEpInInches = 13.37
   fes[1].cores[60].lanes[1].doRxPolaritySwapped = True
   fes[1].cores[60].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[60].lanes[1].traceLengthToNextEpInInches = 11.23
   fes[1].cores[60].lanes[2].doRxPolaritySwapped = False
   fes[1].cores[60].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[60].lanes[2].traceLengthToNextEpInInches = 9.29
   fes[1].cores[60].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[60].lanes[3].doTxPolaritySwapped = False
   fes[1].cores[60].lanes[3].traceLengthToNextEpInInches = 7.13
   fes[1].cores[60].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[60].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[60].lanes[4].traceLengthToNextEpInInches = 9.44
   fes[1].cores[60].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[60].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[60].lanes[5].traceLengthToNextEpInInches = 7.29
   fes[1].cores[60].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[60].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[60].lanes[6].traceLengthToNextEpInInches = 13.18
   fes[1].cores[60].lanes[7].doRxPolaritySwapped = True
   fes[1].cores[60].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[60].lanes[7].traceLengthToNextEpInInches = 11.03
   fes[1].cores[61].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[61].lanes[0].doTxPolaritySwapped = False
   fes[1].cores[61].lanes[0].traceLengthToNextEpInInches = 13.69
   fes[1].cores[61].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[61].lanes[1].doTxPolaritySwapped = True
   fes[1].cores[61].lanes[1].traceLengthToNextEpInInches = 11.53
   fes[1].cores[61].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[61].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[61].lanes[2].traceLengthToNextEpInInches = 8.95
   fes[1].cores[61].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[61].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[61].lanes[3].traceLengthToNextEpInInches = 6.80
   fes[1].cores[61].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[61].lanes[4].doTxPolaritySwapped = False
   fes[1].cores[61].lanes[4].traceLengthToNextEpInInches = 9.14
   fes[1].cores[61].lanes[5].doRxPolaritySwapped = False
   fes[1].cores[61].lanes[5].doTxPolaritySwapped = True
   fes[1].cores[61].lanes[5].traceLengthToNextEpInInches = 6.97
   fes[1].cores[61].lanes[6].doRxPolaritySwapped = True
   fes[1].cores[61].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[61].lanes[6].traceLengthToNextEpInInches = 13.53
   fes[1].cores[61].lanes[7].doRxPolaritySwapped = True
   fes[1].cores[61].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[61].lanes[7].traceLengthToNextEpInInches = 11.38
   fes[1].cores[62].lanes[0].doRxPolaritySwapped = False
   fes[1].cores[62].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[62].lanes[0].traceLengthToNextEpInInches = 15.01
   fes[1].cores[62].lanes[1].doRxPolaritySwapped = True
   fes[1].cores[62].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[62].lanes[1].traceLengthToNextEpInInches = 12.88
   fes[1].cores[62].lanes[2].doRxPolaritySwapped = False
   fes[1].cores[62].lanes[2].doTxPolaritySwapped = False
   fes[1].cores[62].lanes[2].traceLengthToNextEpInInches = 10.98
   fes[1].cores[62].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[62].lanes[3].doTxPolaritySwapped = True
   fes[1].cores[62].lanes[3].traceLengthToNextEpInInches = 8.79
   fes[1].cores[62].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[62].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[62].lanes[4].traceLengthToNextEpInInches = 11.14
   fes[1].cores[62].lanes[5].doRxPolaritySwapped = True
   fes[1].cores[62].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[62].lanes[5].traceLengthToNextEpInInches = 8.95
   fes[1].cores[62].lanes[6].doRxPolaritySwapped = False
   fes[1].cores[62].lanes[6].doTxPolaritySwapped = False
   fes[1].cores[62].lanes[6].traceLengthToNextEpInInches = 14.85
   fes[1].cores[62].lanes[7].doRxPolaritySwapped = True
   fes[1].cores[62].lanes[7].doTxPolaritySwapped = True
   fes[1].cores[62].lanes[7].traceLengthToNextEpInInches = 12.73
   fes[1].cores[63].lanes[0].doRxPolaritySwapped = True
   fes[1].cores[63].lanes[0].doTxPolaritySwapped = True
   fes[1].cores[63].lanes[0].traceLengthToNextEpInInches = 15.36
   fes[1].cores[63].lanes[1].doRxPolaritySwapped = False
   fes[1].cores[63].lanes[1].doTxPolaritySwapped = False
   fes[1].cores[63].lanes[1].traceLengthToNextEpInInches = 13.19
   fes[1].cores[63].lanes[2].doRxPolaritySwapped = True
   fes[1].cores[63].lanes[2].doTxPolaritySwapped = True
   fes[1].cores[63].lanes[2].traceLengthToNextEpInInches = 10.65
   fes[1].cores[63].lanes[3].doRxPolaritySwapped = True
   fes[1].cores[63].lanes[3].doTxPolaritySwapped = False
   fes[1].cores[63].lanes[3].traceLengthToNextEpInInches = 8.50
   fes[1].cores[63].lanes[4].doRxPolaritySwapped = False
   fes[1].cores[63].lanes[4].doTxPolaritySwapped = True
   fes[1].cores[63].lanes[4].traceLengthToNextEpInInches = 10.81
   fes[1].cores[63].lanes[5].doRxPolaritySwapped = False
   fes[1].cores[63].lanes[5].doTxPolaritySwapped = False
   fes[1].cores[63].lanes[5].traceLengthToNextEpInInches = 8.65
   fes[1].cores[63].lanes[6].doRxPolaritySwapped = True
   fes[1].cores[63].lanes[6].doTxPolaritySwapped = True
   fes[1].cores[63].lanes[6].traceLengthToNextEpInInches = 15.18
   fes[1].cores[63].lanes[7].doRxPolaritySwapped = True
   fes[1].cores[63].lanes[7].doTxPolaritySwapped = False
   fes[1].cores[63].lanes[7].traceLengthToNextEpInInches = 13.04
