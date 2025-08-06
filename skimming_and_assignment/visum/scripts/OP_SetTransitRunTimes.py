# replicate Emme TTF in Visum 
# chetan joshi, ptv portland or 2/11/2025
# @luke.gordon, adapted further for LCOG model 2/11/2025

    # a ft1  =timau * 1.15
    # a ft2  =timau * 1.2
    # a ft3  =timau
    # a ft4  =timau * 1.09
    # a ft5  =60 * length / us1
    # a ft6  =60 * length / us1 + 60 * length / 180
    # a ft11 =(timau * 1.15)
    # a ft12 =(timau * 1.3)
    # a ft13 =(timau)
    # a ft14 =(timau * 1.09)
    # a ft15 =(60 * length / us1)
    # a ft16 =(60 * length / us1 + 60 * length / 180)
    # a ft21 =timau * 1.05
    # a ft22 =timau * 1.03

default_speed = 30 #mph -> default speed of transit 

def calc_ttf(ft, timau, length, us1):
    if us1 <= 0:
        us1 = default_speed

    if length:
        transit_time = 3600*length / default_speed

        if timau < 999:
            if ft == 1:
                transit_time = timau * 1.15
            elif ft == 2:
                transit_time = timau * 1.20
            elif ft == 3:
                transit_time = timau
            elif ft == 4:
                transit_time = timau * 1.09
            elif ft == 5:
                transit_time = 60* (60 * length / us1)
            elif ft == 6:
                transit_time = 60* (60 * length / us1 + 60 * length / 180)
            elif ft ==11:
                transit_time = timau * 1.15
            elif ft ==12:
                transit_time = timau * 1.30
            elif ft ==13:
                transit_time = timau
            elif ft ==14:
                transit_time =timau * 1.09
            elif ft == 15:
                transit_time = 60* (60 * length / us1)
            elif ft == 16:
                transit_time = 60* (60 * length / us1 + 60 * length / 180)
            elif ft == 21:
                transit_time = timau * 1.05
            elif ft == 22:
                transit_time = timau * 1.03
    else:
        transit_time = 1

    return transit_time

def update_transit_time():
    tpitems = Visum.Net.TimeProfileItems.GetMultipleAttributes(["LINEROUTEITEM\\EMME_TTFINDEX", "SUM:USEDLINEROUTEITEMS\\OUTLINK\\AddVal2","SUM:USEDLINEROUTEITEMS\\POSTLENGTH", 
                                                                "LINEROUTEITEM\\EMME_DATA1"])
    result  = []
    for ft, timau, length, us1 in tpitems:
        haul_time = calc_ttf(ft, timau, length, us1)
        result.append([haul_time, ])
    
    Visum.Net.TimeProfileItems.SetMultipleAttributes(["AddVal"], result)


update_transit_time()


