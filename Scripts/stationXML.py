from obspy.core.inventory import (Inventory, Network, Station, Channel, Site, 
                                  Response, InstrumentSensitivity, Frequency,
                                  PolesZerosResponseStage,CoefficientsTypeResponseStage)
from obspy.core.util.obspy_types import FloatWithUncertaintiesAndUnit,CustomFloat
from obspy.io.xseed import Parser
from obspy import UTCDateTime
import numpy as np


# This file contains a group of functions which can be used/edited to
# station metadata into the station XML format
# Not for direct use with Lazylyst

# Example Conversion of a station csv file to a station xml file
def staCsv2Xml(staCsvPath,staXmlPath,source='Lazylyst'):
    # Load the csv file
    info=np.genfromtxt(staCsvPath,delimiter=',',dtype=str)
    # For each network... 
    networks=[]
    unqNets=np.unique(info[:,5])
    for net in unqNets:
        netInfo=info[np.where(info[:,5]==net)]
        # ...gather its stations
        stations=[]
        for entry in netInfo:
            stations.append(Station(entry[0],entry[1],entry[2],entry[3],
                                    site=Site(''),creation_date=UTCDateTime(1970, 1, 1)))
        networks.append(Network(net,stations=stations))
    # Generate the inventory object, and save it as a station XML
    inv=Inventory(networks=networks,source=source)
    inv.write(staXmlPath,format='stationxml',validate=True)

# Convert a list of two arrays into one which has uncertainty attached
def genArrWithUncertainty(vals,errs):
    outArr=[FloatWithUncertaintiesAndUnit(val,lower_uncertainty=err,upper_uncertainty=err) 
            for val,err in zip(vals,errs)]
    return outArr

# Collect a station object from a dataless seed station block
def getStation(stationBlock,units,transFuncs):
    ## Should probably do a check up here to see that the order given in block is consistent ##
    for entry in stationBlock:
        if entry.name=='Station Identifier':
#            print 'NewStation!',entry.station_call_letters
            staDict={'code':entry.station_call_letters,
                    'latitude':entry.latitude,
                    'longitude':entry.longitude,
                    'elevation':entry.elevation,
                    'channels':[],
                    'site':Site(entry.site_name),
                    'creation_date':UTCDateTime(entry.start_effective_date), # Allows for save
                    'start_date':UTCDateTime(entry.start_effective_date),
                    'end_date':UTCDateTime(entry.end_effective_date)}
            staNetCode=entry.network_code
        # If found a new channel, reset the stages
        elif entry.name=='Channel Identifier':
#            print 'NewChannel!',entry.channel_identifier
            stages=[]
            chaDict={'code':entry.channel_identifier,
                     'location_code':entry.location_identifier,
                     'latitude':entry.latitude,
                     'longitude':entry.longitude,
                     'elevation':entry.elevation,
                     'depth':entry.local_depth,
                     'sample_rate':entry.sample_rate,
                     'start_date':UTCDateTime(entry.start_date),
                     'end_date':UTCDateTime(entry.end_date),
                     'azimuth':entry.azimuth,
                     'dip':entry.dip}
        #code, location_code, latitude, longitude, elevation, depth
        # If on a new stage, set up the dictionary again
        # ...paz stage
        elif entry.name=='Response Poles and Zeros':
            # Get units
            stageReqs={}
#            print entry.name,entry.stage_sequence_number
#            print entry
#            quit()
            stageReqs['input_units']=units[entry.stage_signal_input_units]
            stageReqs['output_units']=units[entry.stage_signal_output_units]
            # Collect the poles and zeros
            lastType='paz'
            if entry.number_of_complex_zeros==0:
                zeros=np.array([],dtype=float)
            else:
                zeros=np.array(entry.real_zero,dtype=float)+np.array(entry.imaginary_zero,dtype=float)*1j
            if entry.number_of_complex_poles==0:
                poles=np.array([],dtype=float)
            else:
                poles=np.array(entry.real_pole,dtype=float)+np.array(entry.imaginary_pole,dtype=float)*1j
            # Form the paz response dictionary
            pazDict={'pz_transfer_function_type':transFuncs[entry.transfer_function_types],
                     'normalization_factor':entry.A0_normalization_factor,
                     'normalization_frequency':entry.normalization_frequency,
                     'zeros':zeros,
                     'poles':poles}
        # ...coeff stage
        elif entry.name=='Response Coefficients':
            # Get units
            stageReqs={}
#            print entry.name,entry.stage_sequence_number
            stageReqs['input_units']=units[entry.signal_input_units]
            stageReqs['output_units']=units[entry.signal_output_units]
            # Collect the coefficients
            lastType='coef'
            if entry.number_of_denominators==0:
                denom=[]
                denomErr=[]
            else:
                denom=entry.denominator_coefficient
                denomErr=entry.denominator_error
            if entry.number_of_numerators==0:
                numer=[]
                numerErr=[]
            else:
                numer=entry.numerator_coefficient
                numerErr=entry.numerator_error
            # Convert these arrays into lists of numbers which have uncertainty
            denomArr=genArrWithUncertainty(denom,denomErr)
            numerArr=genArrWithUncertainty(numer,numerErr)
            # Form the coeefficient response dictionary
            coefDict={'cf_transfer_function_type':transFuncs[entry.response_type],
                      'numerator':numerArr,
                      'denominator':denomArr}
        # Get the decimation sampling info
        elif entry.name=='Decimation':
#            print entry.name,entry.stage_sequence_number
            stageReqs['decimation_input_sample_rate']=Frequency(entry.input_sample_rate)
            stageReqs['decimation_factor']=entry.decimation_factor
            stageReqs['decimation_offset']=entry.decimation_offset
            stageReqs['decimation_delay']=FloatWithUncertaintiesAndUnit(entry.estimated_delay)
            stageReqs['decimation_correction']=FloatWithUncertaintiesAndUnit(entry.correction_applied)
        # Get the stage sensitivity
        elif entry.name=='Channel Sensitivity Gain':
#            print entry.name,entry.stage_sequence_number
            if entry.stage_sequence_number!=0:
                stageReqs['stage_sequence_number']=entry.stage_sequence_number
                stageReqs['stage_gain']=entry.sensitivity_gain
                stageReqs['stage_gain_frequency']=entry.frequency
                # See what type of stage this was
                if lastType=='paz':
                    pazDict.update(stageReqs)
                    stages.append(PolesZerosResponseStage(**pazDict))
                else:
                    coefDict.update(stageReqs)
                    stages.append(CoefficientsTypeResponseStage(**coefDict))
            # If on the last stage, send off the collected stage info
            else:
                instrSens=InstrumentSensitivity(entry.sensitivity_gain,entry.frequency,
                                                stages[0].input_units,stages[-1].output_units)
                # Finalize the channel dictionary, and append this channel to the station dictionary
                chaResp=Response(response_stages=stages,
                                 instrument_sensitivity=instrSens)
                chaDict['response']=chaResp
                staDict['channels'].append(Channel(**chaDict))
    # Return the stations to the list of stations (also track the network code)
    return Station(**staDict),staNetCode
    
# Convert a dataless seed to a station XML file
def dataless2stationXml(datalessFileName,xmlFileName):
    # Read the dataless seed file
    sp = Parser(datalessFileName)    
    
    # Collect all potential unit abbreviations
    units={}
    #genAbbrev={}
    for entry in sp.abbreviations:
        if entry.name=='Units Abbreviations':
            units[entry.unit_lookup_code]=entry.unit_name
    #    elif entry.name=='Generic Abbreviation':
    #        genAbbrev[entry.abbreviation_lookup_code]=entry.abbreviation_description

    # Make a look-up dictionary for the transfer functions
    transFuncs={'A':'LAPLACE (RADIANS/SECOND)',
                'B':'ANALOG (HERTZ)',
                'C':'COMPOSITE',
                'D':'DIGITAL (Z-TRANSFORM)'}
    
    # Collect each of the stations objects
    stations=[]
    staNetCodes=[]    
    for stationBlock in sp.stations:
        station,staNetCode=getStation(stationBlock,units,transFuncs)
        stations.append(station)
        staNetCodes.append(staNetCode)
        
    # For each of the unique networks codes, collect the stations which relate to it
    networks=[]
    staNetCodes=np.array(staNetCodes)
    unqNets=np.unique(staNetCodes)
    for aNet in unqNets:
        netStas=[stations[arg] for arg in np.where(staNetCodes==aNet)[0]]
        networks.append(Network(aNet,stations=netStas))
    
    # Finally turn this into an inventory and save
    inv=Inventory(networks,'Lazylyst')
    inv.write(xmlFileName,format='stationxml',validate=True)
    

#dataless2stationXml('NX.dataless','NX_Full.xml')    

#    #print inv
#    cha=inv[0][0][0]
#    resp=cha.response
#    resp.plot(0.001)
    
    
# For plotting the response
#from obspy.signal.invsim import paz_to_freq_resp
#poles = [-4.440 + 4.440j, -4.440 - 4.440j, -1.083 + 0.0j]
#zeros = [0.0 + 0.0j, 0.0 + 0.0j, 0.0 + 0.0j]
#scale_fac = 0.4
#h, f = paz_to_freq_resp(poles, zeros, scale_fac, 0.005, 16384, freq=True)
#plt.loglog(f, abs(h))
#plt.xlabel('Frequency [Hz]')
#plt.ylabel('Amplitude')
#phase = np.unwrap(np.arctan2(-h.imag, h.real))
#plt.semilogx(f, phase)


#inv=read_inventory()
#cha=inv[0][0][0]
#resp=cha.response
#resp.plot(0.001)
#quit()



