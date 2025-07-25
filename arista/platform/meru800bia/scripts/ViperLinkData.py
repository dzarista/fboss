#!/usr/bin/env python3
# Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

# Fake Fap and PortData definitions to be able to import trace lengths in
# setFabricLaneTraceLength(), which was provided by diags. Diags uses this code to
# populate their internal Fap object, which we don't have replicate/use in full
# here.
class Fap:
   class PortData:
      traceLengthToNextEpInInches: float
   fabricPorts : list[ PortData ]
   def __init__( self, numFabricPorts ):
      self.fabricPorts = [ self.PortData() for i in range( numFabricPorts ) ]

def fabricTraceLengthByLogicalLane( asicId: int, numFabricPorts: int) -> list[Fap.PortData]:
   # Only one asic per Viper
   assert asicId == 0
   faps = [ Fap(numFabricPorts), ]
   setFabricLaneTraceLength(faps)
   return faps[ asicId ].fabricPorts

def setFabricLaneTraceLength( faps ):
   faps[0].fabricPorts[0].traceLengthToNextEpInInches = 4.98
   faps[0].fabricPorts[1].traceLengthToNextEpInInches = 4.94
   faps[0].fabricPorts[2].traceLengthToNextEpInInches = 4.97
   faps[0].fabricPorts[3].traceLengthToNextEpInInches = 5.03
   faps[0].fabricPorts[4].traceLengthToNextEpInInches = 4.72
   faps[0].fabricPorts[5].traceLengthToNextEpInInches = 4.99
   faps[0].fabricPorts[6].traceLengthToNextEpInInches = 4.84
   faps[0].fabricPorts[7].traceLengthToNextEpInInches = 4.8
   faps[0].fabricPorts[8].traceLengthToNextEpInInches = 5.93
   faps[0].fabricPorts[9].traceLengthToNextEpInInches = 6.43
   faps[0].fabricPorts[10].traceLengthToNextEpInInches = 5.99
   faps[0].fabricPorts[11].traceLengthToNextEpInInches = 6.09
   faps[0].fabricPorts[12].traceLengthToNextEpInInches = 6.31
   faps[0].fabricPorts[13].traceLengthToNextEpInInches = 6.2
   faps[0].fabricPorts[14].traceLengthToNextEpInInches = 6.15
   faps[0].fabricPorts[15].traceLengthToNextEpInInches = 5.97
   faps[0].fabricPorts[16].traceLengthToNextEpInInches = 6.17
   faps[0].fabricPorts[17].traceLengthToNextEpInInches = 6.25
   faps[0].fabricPorts[18].traceLengthToNextEpInInches = 6.25
   faps[0].fabricPorts[19].traceLengthToNextEpInInches = 6.49
   faps[0].fabricPorts[20].traceLengthToNextEpInInches = 6.04
   faps[0].fabricPorts[21].traceLengthToNextEpInInches = 6.17
   faps[0].fabricPorts[22].traceLengthToNextEpInInches = 6.23
   faps[0].fabricPorts[23].traceLengthToNextEpInInches = 6.03
   faps[0].fabricPorts[24].traceLengthToNextEpInInches = 7.27
   faps[0].fabricPorts[25].traceLengthToNextEpInInches = 7.82
   faps[0].fabricPorts[26].traceLengthToNextEpInInches = 7.71
   faps[0].fabricPorts[27].traceLengthToNextEpInInches = 7.42
   faps[0].fabricPorts[28].traceLengthToNextEpInInches = 7.71
   faps[0].fabricPorts[29].traceLengthToNextEpInInches = 7.58
   faps[0].fabricPorts[30].traceLengthToNextEpInInches = 7.47
   faps[0].fabricPorts[31].traceLengthToNextEpInInches = 7.68
   faps[0].fabricPorts[32].traceLengthToNextEpInInches = 6.78
   faps[0].fabricPorts[33].traceLengthToNextEpInInches = 6.79
   faps[0].fabricPorts[34].traceLengthToNextEpInInches = 6.86
   faps[0].fabricPorts[35].traceLengthToNextEpInInches = 6.99
   faps[0].fabricPorts[36].traceLengthToNextEpInInches = 6.98
   faps[0].fabricPorts[37].traceLengthToNextEpInInches = 6.82
   faps[0].fabricPorts[38].traceLengthToNextEpInInches = 6.93
   faps[0].fabricPorts[39].traceLengthToNextEpInInches = 6.95
   faps[0].fabricPorts[40].traceLengthToNextEpInInches = 7.04
   faps[0].fabricPorts[41].traceLengthToNextEpInInches = 7.19
   faps[0].fabricPorts[42].traceLengthToNextEpInInches = 7.47
   faps[0].fabricPorts[43].traceLengthToNextEpInInches = 7.42
   faps[0].fabricPorts[44].traceLengthToNextEpInInches = 7.05
   faps[0].fabricPorts[45].traceLengthToNextEpInInches = 7.15
   faps[0].fabricPorts[46].traceLengthToNextEpInInches = 7.14
   faps[0].fabricPorts[47].traceLengthToNextEpInInches = 7.33
   faps[0].fabricPorts[48].traceLengthToNextEpInInches = 8.49
   faps[0].fabricPorts[49].traceLengthToNextEpInInches = 8.19
   faps[0].fabricPorts[50].traceLengthToNextEpInInches = 8.48
   faps[0].fabricPorts[51].traceLengthToNextEpInInches = 8.21
   faps[0].fabricPorts[52].traceLengthToNextEpInInches = 8.12
   faps[0].fabricPorts[53].traceLengthToNextEpInInches = 8.2
   faps[0].fabricPorts[54].traceLengthToNextEpInInches = 8.16
   faps[0].fabricPorts[55].traceLengthToNextEpInInches = 8.2
   faps[0].fabricPorts[56].traceLengthToNextEpInInches = 9.57
   faps[0].fabricPorts[57].traceLengthToNextEpInInches = 10.0
   faps[0].fabricPorts[58].traceLengthToNextEpInInches = 9.85
   faps[0].fabricPorts[59].traceLengthToNextEpInInches = 10.39
   faps[0].fabricPorts[60].traceLengthToNextEpInInches = 9.92
   faps[0].fabricPorts[61].traceLengthToNextEpInInches = 9.63
   faps[0].fabricPorts[62].traceLengthToNextEpInInches = 9.48
   faps[0].fabricPorts[63].traceLengthToNextEpInInches = 10.15
   faps[0].fabricPorts[64].traceLengthToNextEpInInches = 8.82
   faps[0].fabricPorts[65].traceLengthToNextEpInInches = 8.65
   faps[0].fabricPorts[66].traceLengthToNextEpInInches = 8.85
   faps[0].fabricPorts[67].traceLengthToNextEpInInches = 8.67
   faps[0].fabricPorts[68].traceLengthToNextEpInInches = 8.67
   faps[0].fabricPorts[69].traceLengthToNextEpInInches = 8.87
   faps[0].fabricPorts[70].traceLengthToNextEpInInches = 8.73
   faps[0].fabricPorts[71].traceLengthToNextEpInInches = 8.68
   faps[0].fabricPorts[72].traceLengthToNextEpInInches = 10.44
   faps[0].fabricPorts[73].traceLengthToNextEpInInches = 10.62
   faps[0].fabricPorts[74].traceLengthToNextEpInInches = 10.45
   faps[0].fabricPorts[75].traceLengthToNextEpInInches = 10.87
   faps[0].fabricPorts[76].traceLengthToNextEpInInches = 9.97
   faps[0].fabricPorts[77].traceLengthToNextEpInInches = 10.11
   faps[0].fabricPorts[78].traceLengthToNextEpInInches = 9.95
   faps[0].fabricPorts[79].traceLengthToNextEpInInches = 10.0
   faps[0].fabricPorts[80].traceLengthToNextEpInInches = 4.86
   faps[0].fabricPorts[81].traceLengthToNextEpInInches = 4.67
   faps[0].fabricPorts[82].traceLengthToNextEpInInches = 4.67
   faps[0].fabricPorts[83].traceLengthToNextEpInInches = 4.66
   faps[0].fabricPorts[84].traceLengthToNextEpInInches = 4.76
   faps[0].fabricPorts[85].traceLengthToNextEpInInches = 4.84
   faps[0].fabricPorts[86].traceLengthToNextEpInInches = 4.68
   faps[0].fabricPorts[87].traceLengthToNextEpInInches = 4.79
   faps[0].fabricPorts[88].traceLengthToNextEpInInches = 6.24
   faps[0].fabricPorts[89].traceLengthToNextEpInInches = 6.01
   faps[0].fabricPorts[90].traceLengthToNextEpInInches = 6.25
   faps[0].fabricPorts[91].traceLengthToNextEpInInches = 6.23
   faps[0].fabricPorts[92].traceLengthToNextEpInInches = 5.93
   faps[0].fabricPorts[93].traceLengthToNextEpInInches = 5.67
   faps[0].fabricPorts[94].traceLengthToNextEpInInches = 5.82
   faps[0].fabricPorts[95].traceLengthToNextEpInInches = 6.02
   faps[0].fabricPorts[96].traceLengthToNextEpInInches = 6.33
   faps[0].fabricPorts[97].traceLengthToNextEpInInches = 6.39
   faps[0].fabricPorts[98].traceLengthToNextEpInInches = 6.4
   faps[0].fabricPorts[99].traceLengthToNextEpInInches = 6.48
   faps[0].fabricPorts[100].traceLengthToNextEpInInches = 6.45
   faps[0].fabricPorts[101].traceLengthToNextEpInInches = 6.4
   faps[0].fabricPorts[102].traceLengthToNextEpInInches = 6.45
   faps[0].fabricPorts[103].traceLengthToNextEpInInches = 6.52
   faps[0].fabricPorts[104].traceLengthToNextEpInInches = 6.63
   faps[0].fabricPorts[105].traceLengthToNextEpInInches = 6.71
   faps[0].fabricPorts[106].traceLengthToNextEpInInches = 6.77
   faps[0].fabricPorts[107].traceLengthToNextEpInInches = 6.82
   faps[0].fabricPorts[108].traceLengthToNextEpInInches = 6.76
   faps[0].fabricPorts[109].traceLengthToNextEpInInches = 6.58
   faps[0].fabricPorts[110].traceLengthToNextEpInInches = 6.72
   faps[0].fabricPorts[111].traceLengthToNextEpInInches = 6.77
   faps[0].fabricPorts[112].traceLengthToNextEpInInches = 6.19
   faps[0].fabricPorts[113].traceLengthToNextEpInInches = 6.26
   faps[0].fabricPorts[114].traceLengthToNextEpInInches = 6.24
   faps[0].fabricPorts[115].traceLengthToNextEpInInches = 6.32
   faps[0].fabricPorts[116].traceLengthToNextEpInInches = 6.4
   faps[0].fabricPorts[117].traceLengthToNextEpInInches = 6.16
   faps[0].fabricPorts[118].traceLengthToNextEpInInches = 6.18
   faps[0].fabricPorts[119].traceLengthToNextEpInInches = 6.42
   faps[0].fabricPorts[120].traceLengthToNextEpInInches = 7.41
   faps[0].fabricPorts[121].traceLengthToNextEpInInches = 7.48
   faps[0].fabricPorts[122].traceLengthToNextEpInInches = 7.64
   faps[0].fabricPorts[123].traceLengthToNextEpInInches = 7.39
   faps[0].fabricPorts[124].traceLengthToNextEpInInches = 7.34
   faps[0].fabricPorts[125].traceLengthToNextEpInInches = 7.29
   faps[0].fabricPorts[126].traceLengthToNextEpInInches = 7.38
   faps[0].fabricPorts[127].traceLengthToNextEpInInches = 7.39
   faps[0].fabricPorts[128].traceLengthToNextEpInInches = 8.49
   faps[0].fabricPorts[129].traceLengthToNextEpInInches = 8.7
   faps[0].fabricPorts[130].traceLengthToNextEpInInches = 8.46
   faps[0].fabricPorts[131].traceLengthToNextEpInInches = 8.4
   faps[0].fabricPorts[132].traceLengthToNextEpInInches = 8.46
   faps[0].fabricPorts[133].traceLengthToNextEpInInches = 8.49
   faps[0].fabricPorts[134].traceLengthToNextEpInInches = 8.3
   faps[0].fabricPorts[135].traceLengthToNextEpInInches = 8.43
   faps[0].fabricPorts[136].traceLengthToNextEpInInches = 10.09
   faps[0].fabricPorts[137].traceLengthToNextEpInInches = 10.03
   faps[0].fabricPorts[138].traceLengthToNextEpInInches = 10.25
   faps[0].fabricPorts[139].traceLengthToNextEpInInches = 10.17
   faps[0].fabricPorts[140].traceLengthToNextEpInInches = 9.88
   faps[0].fabricPorts[141].traceLengthToNextEpInInches = 9.49
   faps[0].fabricPorts[142].traceLengthToNextEpInInches = 9.71
   faps[0].fabricPorts[143].traceLengthToNextEpInInches = 9.83
   faps[0].fabricPorts[144].traceLengthToNextEpInInches = 8.63
   faps[0].fabricPorts[145].traceLengthToNextEpInInches = 8.5
   faps[0].fabricPorts[146].traceLengthToNextEpInInches = 8.53
   faps[0].fabricPorts[147].traceLengthToNextEpInInches = 8.6
   faps[0].fabricPorts[148].traceLengthToNextEpInInches = 8.49
   faps[0].fabricPorts[149].traceLengthToNextEpInInches = 8.64
   faps[0].fabricPorts[150].traceLengthToNextEpInInches = 8.49
   faps[0].fabricPorts[151].traceLengthToNextEpInInches = 8.5
   faps[0].fabricPorts[152].traceLengthToNextEpInInches = 9.74
   faps[0].fabricPorts[153].traceLengthToNextEpInInches = 9.82
   faps[0].fabricPorts[154].traceLengthToNextEpInInches = 9.88
   faps[0].fabricPorts[155].traceLengthToNextEpInInches = 10.29
   faps[0].fabricPorts[156].traceLengthToNextEpInInches = 10.09
   faps[0].fabricPorts[157].traceLengthToNextEpInInches = 9.74
   faps[0].fabricPorts[158].traceLengthToNextEpInInches = 10.21
   faps[0].fabricPorts[159].traceLengthToNextEpInInches = 10.23
