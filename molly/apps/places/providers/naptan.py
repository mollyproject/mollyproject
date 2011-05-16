import ftplib, os, urllib, zipfile, tempfile, random, re, csv

from collections import defaultdict
from StringIO import StringIO

from xml.sax import ContentHandler, make_parser

from django.contrib.gis.geos import Point

from molly.apps.places.providers import BaseMapsProvider
from molly.apps.places.models import EntityType, Entity, EntityGroup, Source, EntityTypeCategory
from molly.conf.settings import batch

# TfL don't release a mapping between the station and line codes used for their
# Trackernet service and the NaPTAN database - this adds them manually. The
# dictionary key is the AtcoCode, and then a list of (lineID, stationID) tuples

TUBE_BAKERLOO = 'B'
TUBE_CENTRAL = 'C'
TUBE_DISTRICT = 'D'
TUBE_HAMMERSMITH = 'H'
TUBE_JUBILEE = 'J'
TUBE_METROPOLITAN = 'M'
TUBE_NORTHERN = 'N'
TUBE_PICCADILLY = 'P'
TUBE_VICTORIA = 'V'
TUBE_WATERLOO = 'W'

TUBE_REFERENCES = {
    
    # Acton Town
    '9400ZZLUACT': ((TUBE_DISTRICT, 'ACT'), (TUBE_PICCADILLY, 'ACT'),),
    
    # Aldgate East
    '9400ZZLUADE': ((TUBE_DISTRICT, 'ALE'), (TUBE_HAMMERSMITH, 'ALD'),),
    
    # Aldgate
    '9400ZZLUALD': ((TUBE_HAMMERSMITH, 'ALD'), (TUBE_METROPOLITAN, 'ALD'),),
    
    # Alperton
    '9400ZZLUALP': ((TUBE_PICCADILLY, 'ALP'),),
    
    # Amersham
    '9400ZZLUAMS': ((TUBE_METROPOLITAN, 'AME'),),
    
    # Angel
    '9400ZZLUAGL': ((TUBE_NORTHERN, 'ANG'),),
    
    # Archway
    '9400ZZLUACY': ((TUBE_NORTHERN, 'ARC'),),
    
    # Arnos Grove
    '9400ZZLUASG': ((TUBE_PICCADILLY, 'AGR'),),
    
    # Arsenal
    '9400ZZLUASL': ((TUBE_PICCADILLY, 'ARL'),),
    
    # Baker Street
    '9400ZZLUBST': ((TUBE_BAKERLOO, 'BST'), (TUBE_HAMMERSMITH, 'BST'),
                    (TUBE_JUBILEE, 'BST'), (TUBE_METROPOLITAN, 'BST'),),
    
    # Balham
    '9400ZZLUBLM': ((TUBE_NORTHERN, 'BAL'),),
    
    # Bank
    '9400ZZLUBNK': ((TUBE_CENTRAL, 'BNK'), (TUBE_NORTHERN, 'BNK'),
                    (TUBE_WATERLOO, 'BNK'),),
    
    # Barbican
    '9400ZZLUBBN': ((TUBE_HAMMERSMITH, 'BAR'), (TUBE_METROPOLITAN, 'BAR'),),
    
    # Barkingside
    '9400ZZLUBKE': ((TUBE_CENTRAL, 'BDE'),),
    
    # Barking
    '9400ZZLUBKG': ((TUBE_DISTRICT, 'BKG'), (TUBE_HAMMERSMITH, 'BKG'),
                    (TUBE_METROPOLITAN, 'BKG'),),
    
    # Barons Court
    '9400ZZLUBSC': ((TUBE_DISTRICT, 'BCT'), (TUBE_PICCADILLY, 'BCT'),),
    
    # Bayswater
    '9400ZZLUBWT': ((TUBE_HAMMERSMITH, 'BAY'),),
    
    # Becontree
    '9400ZZLUBEC': ((TUBE_DISTRICT, 'BCT'),),
    
    # Belsize Park
    '9400ZZLUBZP': ((TUBE_NORTHERN, 'BPL'),),
    
    # Bermondsey
    '9400ZZLUBMY': ((TUBE_JUBILEE, 'BER'),),
    
    # Bethnal Green
    '9400ZZLUBLG': ((TUBE_CENTRAL, 'BNG'),),
    
    # Blackfriars
    '9400ZZLUBKF': ((TUBE_DISTRICT, 'BLF'), (TUBE_HAMMERSMITH, 'BLF'),),
    
    # Blackhorse Road
    '9400ZZLUBLR': ((TUBE_VICTORIA, 'BHR'),),
    
    # Bond Street
    '9400ZZLUBND': ((TUBE_CENTRAL, 'BDS'), (TUBE_JUBILEE, 'BDS'),),
    
    # Borough
    '9400ZZLUBOR': ((TUBE_NORTHERN, 'BOR'),),
    
    # Boston Manor
    '9400ZZLUBOS': ((TUBE_PICCADILLY, 'BOS'),),
    
    # Bounds Green
    '9400ZZLUBDS': ((TUBE_PICCADILLY, 'BGR'),),
    
    # Bow Road
    '9400ZZLUBWR': ((TUBE_DISTRICT, 'BWR'), (TUBE_HAMMERSMITH, 'BWR'),),
    
    # Brent Cross
    '9400ZZLUBTX': ((TUBE_NORTHERN, 'BTX'),),
    
    # Brixton
    '9400ZZLUBXN': ((TUBE_VICTORIA, 'BRX'),),
    
    # Bromley-by-Bow
    '9400ZZLUBBB': ((TUBE_DISTRICT, 'BBB'), (TUBE_HAMMERSMITH, 'BBB'),),
    
    # Buckhurst Hill
    '9400ZZLUBKH': ((TUBE_CENTRAL, 'BHL'),),
    
    # Burnt Oak
    '9400ZZLUBTK': ((TUBE_NORTHERN, 'BUR'),),
    
    # Caledonian Road
    '9400ZZLUCAR': ((TUBE_PICCADILLY, 'CRD'),),
    
    # Camden Town
    '9400ZZLUCTN': ((TUBE_NORTHERN, 'CAM'),),
    
    # Canada Water
    '9400ZZLUCWR': ((TUBE_JUBILEE, 'CWR'),),
    
    # Canary Wharf
    '9400ZZLUCYF': ((TUBE_JUBILEE, 'CWF'),),
    
    # Canning Town
    '9400ZZLUCGT': ((TUBE_JUBILEE, 'CNT'),),
    
    # Cannon Street
    '9400ZZLUCST': ((TUBE_DISTRICT, 'CST'), (TUBE_HAMMERSMITH, 'CST'),),
    
    # Canons Park
    '9400ZZLUCPK': (),
    
    # Chalfont & Latimer
    '9400ZZLUCAL': ((TUBE_METROPOLITAN, 'CLF'),),
    
    # Chalk Farm
    '9400ZZLUCFM': ((TUBE_NORTHERN, 'CHF'),),
    
    # Chancery Lane
    '9400ZZLUCHL': ((TUBE_CENTRAL, 'CYL'),),
    
    # Charing Cross
    '9400ZZLUCHX': ((TUBE_BAKERLOO, 'CHX'), (TUBE_NORTHERN, 'CHX'),
                    (TUBE_JUBILEE, 'CHX'),),
    
    # Chesham
    '9400ZZLUCSM': (),
    
    # Chigwell
    '9400ZZLUCWL': ((TUBE_CENTRAL, 'CHG'),),
    
    # Chiswick Park
    '9400ZZLUCWP': ((TUBE_DISTRICT, 'CHP'),),
    
    # Chorleywood
    '9400ZZLUCYD': ((TUBE_METROPOLITAN, 'CWD'),),
    
    # Clapham Common
    '9400ZZLUCPC': ((TUBE_NORTHERN, 'CPC'),),
    
    # Clapham North
    '9400ZZLUCPN': ((TUBE_NORTHERN, 'CPN'),),
    
    # Clapham South
    '9400ZZLUCPS': ((TUBE_NORTHERN, 'CPS'),),
    
    # Cockfosters
    '9400ZZLUCKS': ((TUBE_PICCADILLY, 'CFS'),),
    
    # Colindale
    '9400ZZLUCND': ((TUBE_NORTHERN, 'COL'),),
    
    # Colliers Wood
    '9400ZZLUCSD': ((TUBE_METROPOLITAN, 'CLW'), (TUBE_NORTHERN, 'CLW'),),
    
    # Covent Garden
    '9400ZZLUCGN': ((TUBE_PICCADILLY, 'COV'),),
    
    # Croxley
    '9400ZZLUCXY': ((TUBE_METROPOLITAN, 'CRX'),),
    
    # Dagenham East
    '9400ZZLUDGE': ((TUBE_DISTRICT, 'DGE'),),
    
    # Dagenham Heathway
    '9400ZZLUDGY': ((TUBE_DISTRICT, 'DGH'),),
    
    # Debden
    '9400ZZLUDBN': ((TUBE_CENTRAL, 'DEB'),),
    
    # Dollis Hill
    '9400ZZLUDOH': ((TUBE_JUBILEE, 'DHL'),),
    
    # Ealing Broadway
    '9400ZZLUEBY': ((TUBE_CENTRAL, 'EBY'), (TUBE_DISTRICT, 'EBY'),),
    
    # Ealing Common
    '9400ZZLUECM': ((TUBE_DISTRICT, 'ECM'), (TUBE_PICCADILLY, 'ECM'),),
    
    # Earl's Court
    '9400ZZLUECT': ((TUBE_DISTRICT, 'ECT'), (TUBE_PICCADILLY, 'ECT'),),
    
    # East Acton
    '9400ZZLUEAN': ((TUBE_CENTRAL, 'EAC'),),
    
    # Eastcote
    '9400ZZLUEAE': ((TUBE_METROPOLITAN, 'ETE'), (TUBE_PICCADILLY, 'ETE'),),
    
    # East Finchley
    '9400ZZLUEFY': ((TUBE_NORTHERN, 'EFY'),),
    
    # East Ham
    '9400ZZLUEHM': ((TUBE_DISTRICT, 'EHM'), (TUBE_HAMMERSMITH, 'EHM'),),
    
    # East Putney
    '9400ZZLUEPY': ((TUBE_DISTRICT, 'EPY'),),
    
    # Edgware Road (Bakerloo)
    '9400ZZLUERB': ((TUBE_BAKERLOO, 'ERB'),),
    
    # Edgware Road (Circle Line)
    '9400ZZLUERC': ((TUBE_DISTRICT, 'ERD'), (TUBE_HAMMERSMITH, 'ERD'),),
    
    # Edgware
    '9400ZZLUEGW': ((TUBE_NORTHERN, 'EDG'),),
    
    # Elephant & Castle
    '9400ZZLUEAC': ((TUBE_BAKERLOO, 'ELE'), (TUBE_NORTHERN, 'ELE'),),
    
    # Elm Park
    '9400ZZLUEPK': ((TUBE_DISTRICT, 'EPK'),),
    
    # Embankment
    '9400ZZLUEMB': ((TUBE_BAKERLOO, 'EMB'), (TUBE_DISTRICT, 'EMB'),
                    (TUBE_HAMMERSMITH, 'EMB'), (TUBE_NORTHERN, 'EMB'),),
    
    # Epping
    '9400ZZLUEPG': ((TUBE_CENTRAL, 'EPP'),),
    
    # Euston Square
    '9400ZZLUESQ': ((TUBE_HAMMERSMITH, 'ESQ'), (TUBE_METROPOLITAN, 'ESQ'),),
    
    # Euston
    '9400ZZLUEUS': ((TUBE_NORTHERN, 'EUS'), (TUBE_VICTORIA, 'EUS'),),
    
    # Fairlop
    '9400ZZLUFLP': ((TUBE_CENTRAL, 'FLP'),),
    
    # Farringdon
    '9400ZZLUFCN': ((TUBE_HAMMERSMITH, 'FAR'), (TUBE_METROPOLITAN, 'FAR'),),
    
    # Finchley Central
    '9400ZZLUFYC': ((TUBE_NORTHERN, 'FYC'),),
    
    # Finchley Road
    '9400ZZLUFYR': ((TUBE_JUBILEE, 'FRD'), (TUBE_METROPOLITAN, 'FRD'),),
    
    # Finsbury Park
    '9400ZZLUFPK': ((TUBE_PICCADILLY, 'FPK'), (TUBE_VICTORIA, 'FPK'),),
    
    # Fulham Broadway
    '9400ZZLUFBY': ((TUBE_DISTRICT, 'FBY'),),
    
    # Gants Hill
    '9400ZZLUGTH': ((TUBE_CENTRAL, 'GHL'),),
    
    # Gloucester Road
    '9400ZZLUGTR': ((TUBE_DISTRICT, 'GRD'), (TUBE_HAMMERSMITH, 'GRD'),
                    (TUBE_PICCADILLY, 'GRD'),),
    
    # Golders Green
    '9400ZZLUGGN': ((TUBE_NORTHERN, 'GGR'),),
    
    # Goldhawk Road
    '9400ZZLUGHK': (),
    
    # Goodge Street
    '9400ZZLUGDG': ((TUBE_NORTHERN, 'GST'),),
    
    # Grange Hill
    '9400ZZLUGGH': ((TUBE_CENTRAL, 'GRH'),),
    
    # Great Portland Street
    '9400ZZLUGPS': ((TUBE_HAMMERSMITH, 'GPS'), (TUBE_METROPOLITAN, 'GPS'),),
    
    # Greenford
    '9400ZZLUGFD': ((TUBE_CENTRAL, 'GFD'),),
    
    # Green Park
    '9400ZZLUGPK': ((TUBE_JUBILEE, 'GPK'), (TUBE_PICCADILLY, 'GPK'),
                    (TUBE_VICTORIA, 'GPK'),),
    
    # Gunnersbury
    '9400ZZLUGBY': ((TUBE_DISTRICT, 'GUN'),),
    
    # Hainault
    '9400ZZLUHLT': ((TUBE_CENTRAL, 'HAI'),),
    
    # Hammersmith (Dist&Picc Line)
    '9400ZZLUHSD': ((TUBE_DISTRICT, 'HMD'), (TUBE_PICCADILLY, 'HMD'),),
    
    # Hammersmith (H&C Line)
    '9400ZZLUHSC': ((TUBE_HAMMERSMITH, 'HMS'),),
    
    # Hampstead
    '9400ZZLUHTD': ((TUBE_NORTHERN, 'HMP'),),
    
    # Hanger Lane
    '9400ZZLUHGR': ((TUBE_CENTRAL, 'HLN'),),
    
    # Harlesden
    '9400ZZLUHSN': ((TUBE_BAKERLOO, 'HSD'),),
    
    # Harrow-on-the-Hill
    '9400ZZLUHOH': ((TUBE_METROPOLITAN, 'HOH'),),
    
    # Harrow & Wealdstone
    '9400ZZLUHAW': ((TUBE_BAKERLOO, 'HAW'),),
    
    # Hatton Cross
    '9400ZZLUHNX': ((TUBE_PICCADILLY, 'HTX'),),
    
    # Heathrow Airport Term 1-3
    '9400ZZLUHRC': ((TUBE_PICCADILLY, 'HRC'),),
    
    # Heathrow Airport Terminal 4
    '9400ZZLUHR4': ((TUBE_PICCADILLY, 'HTF'),),
    
    # Heathrow Airport Terminal 5
    '9400ZZLUHR5': ((TUBE_PICCADILLY, 'HRV'),),
    
    # Hendon Central
    '9400ZZLUHCL': ((TUBE_NORTHERN, 'HND'),),
    
    # High Barnet
    '9400ZZLUHBT': ((TUBE_NORTHERN, 'HBT'),),
    
    # Highbury & Islington
    '9400ZZLUHAI': ((TUBE_VICTORIA, 'HBY'),),
    
    # Highgate
    '9400ZZLUHGT': ((TUBE_NORTHERN, 'HIG'),),
    
    # High Street Kensington
    '9400ZZLUHSK': ((TUBE_DISTRICT, 'HST'), (TUBE_HAMMERSMITH, 'HST'),),
    
    # Hillingdon
    '9400ZZLUHGD': ((TUBE_METROPOLITAN, 'HDN'), (TUBE_PICCADILLY, 'HDN'),),
    
    # Holborn
    '9400ZZLUHBN': ((TUBE_CENTRAL, 'HOL'), (TUBE_PICCADILLY, 'HOL'),),
    
    # Holland Park
    '9400ZZLUHPK': ((TUBE_CENTRAL, 'HPK'),),
    
    # Holloway Road
    '9400ZZLUHWY': ((TUBE_PICCADILLY, 'HRD'),),
    
    # Hornchurch
    '9400ZZLUHCH': ((TUBE_DISTRICT, 'HCH'),),
    
    # Hounslow Central
    '9400ZZLUHWC': ((TUBE_PICCADILLY, 'NHC'),),
    
    # Hounslow East
    '9400ZZLUHWE': ((TUBE_PICCADILLY, 'HNE'),),
    
    # Hounslow West
    '9400ZZLUHWT': ((TUBE_PICCADILLY, 'HNW'),),
    
    # Hyde Park Corner
    '9400ZZLUHPC': ((TUBE_PICCADILLY, 'HPC'),),
    
    # Ickenham
    '9400ZZLUICK': ((TUBE_METROPOLITAN, 'ICK'), (TUBE_PICCADILLY, 'ICK'),),
    
    # Kennington
    '9400ZZLUKNG': ((TUBE_NORTHERN, 'KEN'),),
    
    # Kensal Green
    '9400ZZLUKSL': ((TUBE_BAKERLOO, 'KGN'),),
    
    # Kensington (Olympia)
    '9400ZZLUKOY': ((TUBE_DISTRICT, 'OLY'),),
    
    # Kentish Town
    '9400ZZLUKSH': ((TUBE_NORTHERN, 'KTN'),),
    
    # Kenton
    '9400ZZLUKEN': ((TUBE_BAKERLOO, 'KNT'),),
    
    # Kew Gardens
    '9400ZZLUKWG': ((TUBE_DISTRICT, 'KEW'),),
    
    # Kilburn Park
    '9400ZZLUKPK': ((TUBE_BAKERLOO, 'KPK'),),
    
    # Kilburn
    '9400ZZLUKBN': ((TUBE_JUBILEE, 'KIL'),),
    
    # Kingsbury
    '9400ZZLUKBY': ((TUBE_JUBILEE, 'KBY'),),
    
    # King's Cross St. Pancras
    '9400ZZLUKSX': ((TUBE_HAMMERSMITH, 'KXX'), (TUBE_METROPOLITAN, 'KXX'),
                    (TUBE_NORTHERN, 'KXX'), (TUBE_PICCADILLY, 'KXX'),
                    (TUBE_VICTORIA, 'KXX'),),
    
    # Knightsbridge
    '9400ZZLUKNB': ((TUBE_PICCADILLY, 'KNB'),),
    
    # Ladbroke Grove
    '9400ZZLULAD': ((TUBE_HAMMERSMITH, 'LBG'),),
    
    # Lambeth North
    '9400ZZLULBN': ((TUBE_BAKERLOO, 'LAM'),),
    
    # Lancaster Gate
    '9400ZZLULGT': ((TUBE_CENTRAL, 'LAN'),),
    
    # Latimer Road
    '9400ZZLULRD': (),
    
    # Leicester Square
    '9400ZZLULSQ': ((TUBE_NORTHERN, 'LSQ'), (TUBE_PICCADILLY, 'LSQ'),),
    
    # Leytonstone
    '9400ZZLULYS': ((TUBE_CENTRAL, 'LYS'),),
    
    # Leyton
    '9400ZZLULYN': ((TUBE_CENTRAL, 'LEY'),),
    
    # Liverpool Street
    '9400ZZLULVT': ((TUBE_CENTRAL, 'LST'), (TUBE_HAMMERSMITH, 'LST'),
                    (TUBE_METROPOLITAN, 'LST'),),
    
    # London Bridge
    '9400ZZLULNB': ((TUBE_JUBILEE, 'LON'), (TUBE_NORTHERN, 'LON'),),
    
    # Loughton
    '9400ZZLULGN': ((TUBE_CENTRAL, 'LTN'),),
    
    # Maida Vale
    '9400ZZLUMVL': ((TUBE_BAKERLOO, 'MDV'),),
    
    # Manor House
    '9400ZZLUMRH': ((TUBE_PICCADILLY, 'MNR'),),
    
    # Mansion House
    '9400ZZLUMSH': ((TUBE_DISTRICT, 'MAN'), (TUBE_HAMMERSMITH, 'MAN'),),
    
    # Marble Arch
    '9400ZZLUMBA': ((TUBE_CENTRAL, 'MAR'),),
    
    # Marylebone
    '9400ZZLUMYB': ((TUBE_BAKERLOO, 'MYB'),),
    
    # Mile End
    '9400ZZLUMED': ((TUBE_CENTRAL, 'MLE'), (TUBE_DISTRICT, 'MLE'),
                    (TUBE_HAMMERSMITH, 'MLE'),),
    
    # Mill Hill East
    '9400ZZLUMHL': ((TUBE_NORTHERN, 'MHE'),),
    
    # Monument
    '9400ZZLUMMT': ((TUBE_DISTRICT, 'MON'), (TUBE_HAMMERSMITH, 'MON'),),
    
    # Moorgate
    '9400ZZLUMGT': ((TUBE_HAMMERSMITH, 'MGT'), (TUBE_METROPOLITAN, 'MGT'),
                    (TUBE_NORTHERN, 'MGT'),),
    
    # Moor Park
    '9400ZZLUMPK': ((TUBE_METROPOLITAN, 'MPK'),),
    
    # Morden
    '9400ZZLUMDN': ((TUBE_NORTHERN, 'MOR'),),
    
    # Mornington Crescent
    '9400ZZLUMTC': ((TUBE_NORTHERN, 'MCR'),),
    
    # Neasden
    '9400ZZLUNDN': ((TUBE_JUBILEE, 'NEA'),),
    
    # Newbury Park
    '9400ZZLUNBP': ((TUBE_CENTRAL, 'NEP'),),
    
    # North Acton
    '9400ZZLUNAN': ((TUBE_CENTRAL, 'NAC'),),
    
    # North Ealing
    '9400ZZLUNEN': ((TUBE_PICCADILLY, 'NEL'),),
    
    # Northfields
    '9400ZZLUNFD': ((TUBE_PICCADILLY, 'NFD'),),
    
    # North Greenwich
    '9400ZZLUNGW': ((TUBE_JUBILEE, 'NGW'),),
    
    # North Harrow
    '9400ZZLUNHA': ((TUBE_METROPOLITAN, 'NHR'),),
    
    # Northolt
    '9400ZZLUNHT': ((TUBE_CENTRAL, 'NHT'),),
    
    # North Wembley
    '9400ZZLUNWY': ((TUBE_BAKERLOO, 'NWM'),),
    
    # Northwick Park
    '9400ZZLUNKP': ((TUBE_METROPOLITAN, 'NWP'),),
    
    # Northwood Hills
    '9400ZZLUNWH': ((TUBE_METROPOLITAN, 'NWH'),),
    
    # Northwood
    '9400ZZLUNOW': ((TUBE_METROPOLITAN, 'NWD'),),
    
    # Notting Hill Gate
    '9400ZZLUNHG': ((TUBE_CENTRAL, 'NHG'), (TUBE_HAMMERSMITH, 'NHG'),),
    
    # Oakwood
    '9400ZZLUOAK': ((TUBE_PICCADILLY, 'OAK'),),
    
    # Old Street
    '9400ZZLUODS': ((TUBE_NORTHERN, 'OLD'),),
    
    # Osterley
    '9400ZZLUOSY': ((TUBE_PICCADILLY, 'OST'),),
    
    # Oval
    '9400ZZLUOVL': ((TUBE_NORTHERN, 'OVL'),),
    
    # Oxford Circus
    '9400ZZLUOXC': ((TUBE_BAKERLOO, 'OXC'), (TUBE_CENTRAL, 'OXC'),
                    (TUBE_VICTORIA, 'OXC'),),
    
    # Paddington (H&C)
    '9400ZZLUPAH': ((TUBE_HAMMERSMITH, 'PAD'),),
    
    # Paddington
    '9400ZZLUPAC': ((TUBE_BAKERLOO, 'PAD'),),
    
    # Park Royal
    '9400ZZLUPKR': ((TUBE_PICCADILLY, 'PRY'),),
    
    # Parsons Green
    '9400ZZLUPSG': ((TUBE_DISTRICT, 'PGR'),),
    
    # Perivale
    '9400ZZLUPVL': ((TUBE_CENTRAL, 'PER'),),
    
    # Piccadilly Circus
    '9400ZZLUPCC': ((TUBE_BAKERLOO, 'PIC'), (TUBE_PICCADILLY, 'PIC'), ),
    
    # Pimlico
    '9400ZZLUPCO': ((TUBE_VICTORIA, 'PIM'),),
    
    # Pinner
    '9400ZZLUPNR': ((TUBE_METROPOLITAN, 'PIN'),),
    
    # Plaistow
    '9400ZZLUPLW': ((TUBE_DISTRICT, 'PLW'), (TUBE_HAMMERSMITH, 'PLW'),),
    
    # Preston Road
    '9400ZZLUPRD': (),
    
    # Putney Bridge
    '9400ZZLUPYB': ((TUBE_DISTRICT, 'PUT'),),
    
    # Queensbury
    '9400ZZLUQBY': ((TUBE_JUBILEE, 'QBY'),),
    
    # Queen's Park
    '9400ZZLUQPS': ((TUBE_BAKERLOO, 'QPK'),),
    
    # Queensway
    '9400ZZLUQWY': ((TUBE_CENTRAL, 'QWY'),),
    
    # Ravenscourt Park
    '9400ZZLURVP': ((TUBE_DISTRICT, 'RCP'),),
    
    # Rayners Lane
    '9400ZZLURYL': ((TUBE_METROPOLITAN, 'RLN'), (TUBE_PICCADILLY, 'RLN'),),
    
    # Redbridge
    '9400ZZLURBG': ((TUBE_CENTRAL, 'RED'),),
    
    # Regent's Park
    '9400ZZLURGP': ((TUBE_BAKERLOO, 'RPK'),),
    
    # Richmond
    '9400ZZLURMD': ((TUBE_DISTRICT, 'RMD'),),
    
    # Rickmansworth
    '9400ZZLURKW': ((TUBE_METROPOLITAN, 'RKY'),),
    
    # Roding Valley
    '9400ZZLURVY': ((TUBE_CENTRAL, 'ROD'),),
    
    # Royal Oak
    '9400ZZLURYO': ((TUBE_HAMMERSMITH, 'ROA'),),
    
    # Ruislip Gardens
    '9400ZZLURSG': ((TUBE_CENTRAL, 'RUG'),),
    
    # Ruislip Manor
    '9400ZZLURSM': ((TUBE_METROPOLITAN, 'RUM'), (TUBE_PICCADILLY, 'RUI'),),
    
    # Ruislip
    '9400ZZLURSP': ((TUBE_METROPOLITAN, 'RUI'), (TUBE_PICCADILLY, 'RUI'),),
    
    # Russell Square
    '9400ZZLURSQ': ((TUBE_PICCADILLY, 'RSQ'),),
    
    # Seven Sisters
    '9400ZZLUSVS': ((TUBE_VICTORIA, 'SVS'),),
    
    # Shepherd's Bush (Central)
    '9400ZZLUSBC': ((TUBE_CENTRAL, 'SBC'),),
    
    # Shepherd's Bush Market
    '9400ZZLUSBM': (),
    
    # Sloane Square
    '9400ZZLUSSQ': ((TUBE_DISTRICT, 'SSQ'), (TUBE_HAMMERSMITH, 'SSQ'),),
    
    # Snaresbrook
    '9400ZZLUSNB': ((TUBE_CENTRAL, 'SNB'),),
    
    # South Ealing
    '9400ZZLUSEA': ((TUBE_PICCADILLY, 'SEL'),),
    
    # Southfields
    '9400ZZLUSFS': ((TUBE_DISTRICT, 'SFS'),),
    
    # Southgate
    '9400ZZLUSGT': ((TUBE_PICCADILLY, 'SGT'),),
    
    # South Harrow
    '9400ZZLUSHH': ((TUBE_PICCADILLY, 'SHR'),),
    
    # South Kensington
    '9400ZZLUSKS': ((TUBE_DISTRICT, 'SKN'), (TUBE_HAMMERSMITH, 'SKN'),
                    (TUBE_PICCADILLY, 'SKN'),),
    
    # South Kenton
    '9400ZZLUSKT': ((TUBE_BAKERLOO, 'SKT'),),
    
    # South Ruislip
    '9400ZZLUSRP': ((TUBE_CENTRAL, 'SRP'),),
    
    # Southwark
    '9400ZZLUSWK': ((TUBE_JUBILEE, 'SWK'),),
    
    # South Wimbledon
    '9400ZZLUSWN': ((TUBE_NORTHERN, 'SWM'),),
    
    # South Woodford
    '9400ZZLUSWF': ((TUBE_CENTRAL, 'SWF'),),
    
    # Stamford Brook
    '9400ZZLUSFB': ((TUBE_DISTRICT, 'STB'),),
    
    # Stanmore
    '9400ZZLUSTM': ((TUBE_JUBILEE, 'STA'),),
    
    # Stepney Green
    '9400ZZLUSGN': ((TUBE_DISTRICT, 'STG'), (TUBE_HAMMERSMITH, 'STG'),),
    
    # St. James's Park
    '9400ZZLUSJP': ((TUBE_DISTRICT, 'SJP'), (TUBE_HAMMERSMITH, 'SJP'),),
    
    # St. John's Wood
    '9400ZZLUSJW': ((TUBE_JUBILEE, 'SJW'),),
    
    # Stockwell
    '9400ZZLUSKW': ((TUBE_NORTHERN, 'STK'), (TUBE_VICTORIA, 'STK'),),
    
    # Stonebridge Park
    '9400ZZLUSGP': ((TUBE_BAKERLOO, 'SPK'),),
    
    # St. Paul's
    '9400ZZLUSPU': ((TUBE_CENTRAL, 'STP'),),
    
    # Stratford
    '9400ZZLUSTD': ((TUBE_CENTRAL, 'SFD'), (TUBE_JUBILEE, 'SFD'),),
    
    # Sudbury Hill
    '9400ZZLUSUH': ((TUBE_PICCADILLY, 'SHL'),),
    
    # Sudbury Town
    '9400ZZLUSUT': ((TUBE_PICCADILLY, 'STN'),),
    
    # Swiss Cottage
    '9400ZZLUSWC': ((TUBE_JUBILEE, 'SWC'),),
    
    # Temple
    '9400ZZLUTMP': ((TUBE_DISTRICT, 'TEM'), (TUBE_HAMMERSMITH, 'TEM'),),
    
    # Theydon Bois
    '9400ZZLUTHB': ((TUBE_CENTRAL, 'THB'),),
    
    # Tooting Bec
    '9400ZZLUTBC': ((TUBE_NORTHERN, 'TBE'),),
    
    # Tooting Broadway
    '9400ZZLUTBY': ((TUBE_NORTHERN, 'TBY'),),
    
    # Tottenham Court Road
    '9400ZZLUTCR': ((TUBE_CENTRAL, 'TCR'), (TUBE_NORTHERN, 'TCR'),),
    
    # Tottenham Hale
    '9400ZZLUTMH': ((TUBE_VICTORIA, 'TTH'),),
    
    # Totteridge & Whetstone
    '9400ZZLUTAW': ((TUBE_NORTHERN, 'TOT'),),
    
    # Tower Hill
    '9400ZZLUTWH': ((TUBE_DISTRICT, 'THL'), (TUBE_HAMMERSMITH, 'THL'),),
    
    # Tufnell Park
    '9400ZZLUTFP': ((TUBE_NORTHERN, 'TPK'),),
    
    # Turnham Green
    '9400ZZLUTNG': ((TUBE_DISTRICT, 'TGR'), (TUBE_PICCADILLY, 'TGR'),),
    
    # Turnpike Lane
    '9400ZZLUTPN': ((TUBE_PICCADILLY, 'TPL'),),
    
    # Upminster Bridge
    '9400ZZLUUPB': ((TUBE_DISTRICT, 'UPM'),),
    
    # Upminster
    '9400ZZLUUPM': (),
    
    # Upney
    '9400ZZLUUPY': ((TUBE_DISTRICT, 'UPY'),),
    
    # Upton Park
    '9400ZZLUUPK': ((TUBE_DISTRICT, 'UPK'), (TUBE_HAMMERSMITH, 'UPK'),),
    
    # Uxbridge
    '9400ZZLUUXB': ((TUBE_METROPOLITAN, 'UXB'), (TUBE_PICCADILLY, 'UXB'),),
    
    # Vauxhall
    '9400ZZLUVXL': ((TUBE_VICTORIA, 'VUX'),),
    
    # Victoria
    '9400ZZLUVIC': ((TUBE_DISTRICT, 'VIC'), (TUBE_HAMMERSMITH, 'VIC'),
                    (TUBE_VICTORIA, 'VIC'),),
    
    # Walthamstow Central
    '9400ZZLUWWL': ((TUBE_VICTORIA, 'WAL'),),
    
    # Wanstead
    '9400ZZLUWSD': ((TUBE_CENTRAL, 'WAN'),),
    
    # Warren Street
    '9400ZZLUWRR': ((TUBE_NORTHERN, 'WST'), (TUBE_VICTORIA, 'WST'),),
    
    # Warwick Avenue
    '9400ZZLUWKA': ((TUBE_BAKERLOO, 'WAR'),),
    
    # Waterloo
    '9400ZZLUWLO': ((TUBE_BAKERLOO, 'WLO'), (TUBE_JUBILEE, 'WLO'),
                    (TUBE_NORTHERN, 'WLO'), (TUBE_WATERLOO, 'WLO'),),
    
    # Watford
    '9400ZZLUWAF': ((TUBE_METROPOLITAN, 'WAT'),),
    
    # Wembley Central
    '9400ZZLUWYC': ((TUBE_BAKERLOO, 'WEM'),),
    
    # Wembley Park
    '9400ZZLUWYP': ((TUBE_JUBILEE, 'WPK'), (TUBE_METROPOLITAN, 'WPK'),),
    
    # West Acton
    '9400ZZLUWTA': ((TUBE_CENTRAL, 'WAC'),),
    
    # Westbourne Park
    '9400ZZLUWSP': ((TUBE_HAMMERSMITH, 'WBP'),),
    
    # West Brompton
    '9400ZZLUWBN': ((TUBE_DISTRICT, 'WBT'),),
    
    # West Finchley
    '9400ZZLUWFN': ((TUBE_NORTHERN, 'WFY'),),
    
    # West Hampstead
    '9400ZZLUWHP': ((TUBE_JUBILEE, 'WHD'),),
    
    # West Ham
    '9400ZZLUWHM': ((TUBE_DISTRICT, 'WHM'), (TUBE_HAMMERSMITH, 'WHM'),
                    (TUBE_JUBILEE, 'WHM'),),
    
    # West Harrow
    '9400ZZLUWHW': ((TUBE_METROPOLITAN, 'WHR'),),
    
    # West Kensington
    '9400ZZLUWKN': ((TUBE_DISTRICT, 'WKN'),),
    
    # Westminster
    '9400ZZLUWSM': ((TUBE_DISTRICT, 'WMS'), (TUBE_HAMMERSMITH, 'WMS'),
                    (TUBE_JUBILEE, 'WMS'),),
    
    # West Ruislip
    '9400ZZLUWRP': ((TUBE_CENTRAL, 'WRP'),),
    
    # Whitechapel
    '9400ZZLUWPL': ((TUBE_DISTRICT, 'WCL'), (TUBE_HAMMERSMITH, 'WCL'),
                    (TUBE_METROPOLITAN, 'WCL'),),
    
    # White City
    '9400ZZLUWCY': ((TUBE_CENTRAL, 'WCT'),),
    
    # Willesden Green
    '9400ZZLUWIG': ((TUBE_JUBILEE, 'WLG'),),
    
    # Willesden Junction
    '9400ZZLUWJN': ((TUBE_BAKERLOO, 'WJN'),),
    
    # Wimbledon Park
    '9400ZZLUWIP': ((TUBE_DISTRICT, 'WMP'),),
    
    # Wimbledon
    '9400ZZLUWIM': ((TUBE_DISTRICT, 'WDN'),),
    
    # Woodford
    '9400ZZLUWOF': ((TUBE_CENTRAL, 'WFD'),),
    
    # Wood Green
    '9400ZZLUWOG': ((TUBE_PICCADILLY, 'WGN'),),
    
    # Wood Lane
    '9400ZZLUWLA': (),
    
    # Woodside Park
    '9400ZZLUWOP': ((TUBE_NORTHERN, 'WSP'), (TUBE_METROPOLITAN, 'WSP'),),
    
}

class NaptanContentHandler(ContentHandler):

    meta_names = {
        ('AtcoCode',): 'atco-code',
        ('NaptanCode',): 'naptan-code',
        ('PlateCode',): 'plate-code',
        ('Descriptor','CommonName'): 'common-name',
        ('Descriptor','Indicator'): 'indicator',
        ('Descriptor','Street'): 'street',
        ('Place','NptgLocalityRef'): 'locality-ref',
        ('Place','Location','Translation','Longitude'): 'longitude',
        ('Place','Location','Translation','Latitude'): 'latitude',
        ('AdministrativeAreaRef',): 'area',
        ('StopAreas', 'StopAreaRef'): 'stop-area',
        ('StopClassification', 'StopType'): 'stop-type',
        ('StopClassification', 'OffStreet', 'Rail', 'AnnotatedRailRef', 'CrsRef'): 'crs',
        ('StopAreaCode',): 'area-code',
        ('Name',): 'name',
    }

    @staticmethod
    def naptan_dial(c):
        """
        Convert a alphabetical NaPTAN code in the database to the numerical code
        used on bus stops
        """
        if c.isdigit():
            return c
        return unicode(min(9, (ord(c)-91)//3))

    def __init__(self, entity_types, source, nptg_localities = None, areas=None):
        self.name_stack = []
        self.entity_types, self.source = entity_types, source
        self.entities = set()
        self.nptg_localities = {} if nptg_localities is None else nptg_localities
        self.areas = areas

    def startElement(self, name, attrs):
        self.name_stack.append(name)

        if name == 'StopPoint':
            self.stop_areas = []
            self.meta = defaultdict(str)
        elif name == 'StopArea':
            self.meta = defaultdict(str)

    def endElement(self, name):
        self.name_stack.pop()

        if name == 'StopPoint':
            try:
                # Classify metro stops according to their particular system
                if self.meta['stop-type'] == 'MET':
                    try:
                        entity_type = self.entity_types[self.meta['stop-type'] + ':' + self.meta['atco-code'][6:8]]
                    except KeyError:
                        entity_type = self.entity_types['MET']
                else:
                    entity_type = self.entity_types[self.meta['stop-type']]
            except KeyError:
                pass
            else:
                entity = self.add_stop(self.meta, entity_type, self.source)
                if entity:
                    self.entities.add(entity)
        elif name == 'StopAreaRef':
            self.stop_areas.append(self.meta['stop-area'])
            del self.meta['stop-area']
        
        elif name == 'StopArea':
            if self.areas != None:
                in_area = False
                for area in self.areas:
                    if self.meta['area-code'].startswith(area):
                        in_area = True
                if not in_area:
                    return
            
            sa, created = EntityGroup.objects.get_or_create(
                source=self.source,
                ref_code=self.meta['area-code'])
            sa.title = self.meta['name']
            sa.save()

    def endDocument(self):
        pass

    def characters(self, text):
        top = tuple(self.name_stack[3:])

        try:
            self.meta[self.meta_names[top]] += text
        except KeyError:
            pass

    def add_stop(self, meta, entity_type, source):
        
        # Check this entity is in an area
        if self.areas != None:
            in_area = False
            for area in self.areas:
                if meta['atco-code'].startswith(area):
                    in_area = True
            if not in_area:
                return
        
        # See if we're updating an existing object, or creating a new one
        try:
            entity = Entity.objects.get(source=source,
                                        _identifiers__scheme='atco',
                                        _identifiers__value=meta['atco-code'])
        except Entity.DoesNotExist:
            entity = Entity(source=source)
        except Entity.MultipleObjectsReturned:
            # Handle clashes
            Entity.objects.filter(source=source,
                                 _identifiers__scheme='atco',
                                 _identifiers__value=meta['atco-code']).delete()
            entity = Entity(source=source)
        
        common_name, indicator, locality, street = [meta.get(k) for k in
                    ('common-name', 'indicator', 'locality-ref', 'street')]
        
        if (common_name or '').endswith(' DEL') or \
          (indicator or '').lower() == 'not in use':
            # In the NaPTAN list, but indicates it's an unused stop
            return
        
        if self.meta['stop-type'] in ('MET','GAT','FER', 'RLY'):
            title = common_name
        else:
        
            # Convert indicator to a friendlier format
            indicator = {
                'opp': 'Opposite',
                'opposite': 'Opposite',
                'adj': 'Adjacent',
                'outside': 'Outside',
                'o/s': 'Outside',
                'nr': 'Near',
                'inside': 'Inside',
            }.get(indicator, indicator)
            
            if indicator is None and self.meta['stop-type'] in ('AIR', 'FTD', 'RSE', 'TMU', 'BCE'):
                indicator = 'Entrance to'
            
            if indicator is None and self.meta['stop-type'] in ('FBT',):
                indicator = 'Berth at'
            
            if indicator is None and self.meta['stop-type'] in ('RPL','PLT'):
                indicator = 'Platform at'
            
            title = ''
            
            if indicator != None:
                title += indicator + ' '
            
            title += common_name
            
            if street != None and street != '-' \
                         and not common_name.startswith(street):
                title += ', ' + street
            
            locality = self.nptg_localities.get(locality)
            if locality != None:
                title += ', ' + locality
        
        entity.title = title
        entity.primary_type = entity_type

        if not entity.metadata:
            entity.metadata = {}
        entity.metadata['naptan'] = meta
        entity.location = Point(float(meta['longitude']), float(meta['latitude']), srid=4326)
        entity.geometry = entity.location
        
        if meta['atco-code'] in TUBE_REFERENCES:
            entity.metadata['london-underground-identifiers'] = TUBE_REFERENCES[meta['atco-code']]
        
        identifiers = {
            'atco': meta['atco-code'],
        }
        if 'naptan-code' in meta:
            meta['naptan-code'] = ''.join(map(self.naptan_dial, meta['naptan-code']))
            identifiers['naptan'] = meta['naptan-code']
        if 'plate-code' in meta:
            identifiers['plate'] = meta['plate-code']
        if 'crs' in meta:
            identifiers['crs'] = meta['crs']
        if indicator != None and re.match('Stop [A-Z]\d\d?', indicator):
            identifiers['stop'] = indicator[5:]
        
        
        entity.save(identifiers=identifiers)
        entity.all_types = (entity_type,)
        
        entity.update_all_types_completion()
        
        entity.groups.clear()
        for stop_area in self.stop_areas:
            sa, created = EntityGroup.objects.get_or_create(source=source, ref_code=stop_area)
            entity.groups.add(sa)
        
        return entity


class NaptanMapsProvider(BaseMapsProvider):

    HTTP_URL = "http://www.dft.gov.uk/NaPTAN/snapshot/NaPTANxml.zip"
    HTTP_CSV_URL = "http://www.dft.gov.uk/NaPTAN/snapshot/NaPTANcsv.zip"
    HTTP_NTPG_URL = "http://www.dft.gov.uk/nptg/snapshot/nptgcsv.zip"
    FTP_SERVER = 'journeyweb.org.uk'
    TRAIN_STATION = object()
    BUS_STOP_DEFINITION = {
            'slug': 'bus-stop',
            'article': 'a',
            'verbose-name': 'bus stop',
            'verbose-name-plural': 'bus stops',
            'nearby': True, 'category': False,
            'uri-local': 'BusStop',
        }
    TAXI_RANK_DEFINITION = {
        'slug': 'taxi-rank',
        'article': 'a',
        'verbose-name': 'taxi rank',
        'verbose-name-plural': 'taxi ranks',
        'nearby': False, 'category': False,
        'uri-local': 'TaxiRank',
    }
    RAIL_STATION_DEFINITION = {
            'slug': 'rail-station',
            'article': 'a',
            'verbose-name': 'rail station',
            'verbose-name-plural': 'rail stations',
            'nearby': True, 'category': False,
            'uri-local': 'RailStation',
        }
    HERITAGE_RAIL_STATION_DEFINITION = {
            'slug': 'heritage-rail-station',
            'article': 'a',
            'verbose-name': 'heritage rail station',
            'verbose-name-plural': 'heritage rail stations',
            'nearby': True, 'category': False,
            'uri-local': 'HeritageRailStation',
        }

    entity_type_definitions = {
        'BCT': BUS_STOP_DEFINITION,
        'BCS': BUS_STOP_DEFINITION,
        'BCQ': BUS_STOP_DEFINITION,
        'BSE': {
            'slug': 'bus-station-entrance',
            'article': 'a',
            'verbose-name': 'bus station entrance',
            'verbose-name-plural': 'bus station entrances',
            'nearby': False, 'category': False,
            'uri-local': 'BusStationEntrance',
        },
        'TXR': TAXI_RANK_DEFINITION,
        'STR': TAXI_RANK_DEFINITION,
        'RLY': RAIL_STATION_DEFINITION,
        'RSE': {
            'slug': 'rail-station-entrance',
            'article': 'a',
            'verbose-name': 'rail station entrance',
            'verbose-name-plural': 'rail station entrances',
            'nearby': False, 'category': False,
            'uri-local': 'RailStationEntrance',
        },
        'RPL': {
            'slug': 'rail-platform',
            'article': 'a',
            'verbose-name': 'rail platform',
            'verbose-name-plural': 'rail platform',
            'nearby': False, 'category': False,
            'uri-local': 'RailPlatform',
        },
        'TMU': {
            'slug': 'metro-entrance',
            'article': 'a',
            'verbose-name': 'metro entrance',
            'verbose-name-plural': 'metro entrances',
            'nearby': False, 'category': False,
            'uri-local': 'MetroEntrance',
        },
        'PLT': {
            'slug': 'platform',
            'article': 'a',
            'verbose-name': 'platform',
            'verbose-name-plural': 'platforms',
            'nearby': False, 'category': False,
            'uri-local': 'MetroPlatform',
        },
        'MET': {
            'slug': 'metro-station',
            'article': 'a',
            'verbose-name': 'metro station',
            'verbose-name-plural': 'metro stations',
            'nearby': True, 'category': False,
            'uri-local': 'MetroStation',
        },
        'MET:AV': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:BB': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:BF': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:BK': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:BL': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:BP': {
            'slug': 'tramway-stop',
            'article': 'a',
            'verbose-name': 'tramway stop',
            'verbose-name-plural': 'tramway stops',
            'nearby': True, 'category': False,
            'uri-local': 'TramwayStop',
        },
        'MET:BV': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:CA': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:CR': {
            'slug': 'tramlink-stop',
            'article': 'a',
            'verbose-name': 'tram stop',
            'verbose-name-plural': 'tram stops',
            'nearby': True, 'category': False,
            'uri-local': 'TramlinkStop',
        },
        'MET:CV': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:CW': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:DF': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:DL': {
            'slug': 'dlr-station',
            'article': 'a',
            'verbose-name': 'DLR station',
            'verbose-name-plural': 'DLR stations',
            'nearby': True, 'category': False,
            'uri-local': 'DLRStation',
        },
        'MET:DM': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:EB': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:EK': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:EL': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:EV': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:FB': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:FF': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:GC': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:GL': {
            'slug': 'subway-station',
            'article': 'a',
            'verbose-name': 'Subway station',
            'verbose-name-plural': 'Subway stations',
            'nearby': True, 'category': False,
            'uri-local': 'SubwayStation',
        },
        'MET:GO': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:GW': {
            'slug': 'shuttle-station',
            'article': 'a',
            'verbose-name': 'shuttle station',
            'verbose-name-plural': 'shuttle station',
            'nearby': True, 'category': False,
            'uri-local': 'ShuttleStation',
        },
        'MET:GR': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:IW': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:KD': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:KE': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:KW': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:LH': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:LL': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:LU': {
            'slug': 'tube-station',
            'article': 'an',
            'verbose-name': 'Underground station',
            'verbose-name-plural': 'Underground stations',
            'nearby': True, 'category': False,
            'uri-local': 'TubeStation',
        },
        'MET:MA': {
            'slug': 'metrolink-station',
            'article': 'a',
            'verbose-name': 'Metrolink station',
            'verbose-name-plural': 'Metrolink stations',
            'nearby': True, 'category': False,
            'uri-local': 'MetrolinkStation',
        },
        'MET:MH': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:MN': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:NN': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:NO': {
            'slug': 'net-stop',
            'article': 'a',
            'verbose-name': 'tram stop',
            'verbose-name-plural': 'tram stops',
            'nearby': True, 'category': False,
            'uri-local': 'NETStop',
        },
        'MET:NV': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:NY': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:PD': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:PR': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:RE': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:RH': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:SD': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:SL': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:SM': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:SP': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:SR': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:ST': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:SV': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:SY': {
            'slug': 'supertram-stop',
            'article': 'a',
            'verbose-name': 'Supertram stop',
            'verbose-name-plural': 'Supertram stops',
            'nearby': True, 'category': False,
            'uri-local': 'SupertramStop',
        },
        'MET:TL': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:TW': {
            'slug': 'tyne-and-wear-metro-station',
            'article': 'a',
            'verbose-name': 'Metro station',
            'verbose-name-plural': 'Metro stations',
            'nearby': True, 'category': False,
            'uri-local': 'TyneAndWearMetroStation',
        },
        'MET:TY': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:VR': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:WD': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:WH': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:WL': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:WM': {
            'slug': 'midland-metro-stop',
            'article': 'a',
            'verbose-name': 'Midland Metro stop',
            'verbose-name-plural': 'Midland Metro stops',
            'nearby': True, 'category': False,
            'uri-local': 'MidlandMetroStation',
        },
        'MET:WS': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:WW': HERITAGE_RAIL_STATION_DEFINITION,
        'GAT': {
            'slug': 'airport',
            'article': 'an',
            'verbose-name': 'airport',
            'verbose-name-plural': 'airports',
            'nearby': True, 'category': False,
            'uri-local': 'Airport',
        },
        'AIR': {
            'slug': 'airport-entrance',
            'article': 'an',
            'verbose-name': 'airport entrance',
            'verbose-name-plural': 'airport entrances',
            'nearby': False, 'category': False,
            'uri-local': 'AirportEntrance',
        },
        'FER': {
            'slug': 'ferry-terminal',
            'article': 'a',
            'verbose-name': 'ferry terminal',
            'verbose-name-plural': 'ferry terminals',
            'nearby': True, 'category': False,
            'uri-local': 'FerryTerminal',
        },
        'FTD': {
            'slug': 'ferry-terminal-entrance',
            'article': 'a',
            'verbose-name': 'ferry terminal entrance',
            'verbose-name-plural': 'ferry terminal entrances',
            'nearby': False, 'category': False,
            'uri-local': 'FerryTerminalEntrance',
        },
        'FBT': {
            'slug': 'ferry-berth',
            'article': 'a',
            'verbose-name': 'ferry berth',
            'verbose-name-plural': 'ferry berths',
            'nearby': False, 'category': False,
            'uri-local': 'FerryBerth',
        },
        None: {
            'slug': 'public-transport-access-node',
            'article': 'a',
            'verbose-name': 'public transport access node',
            'verbose-name-plural': 'public transport access nodes',
            'nearby': False, 'category': False,
            'uri-local': 'PublicTransportAccessNode',
        }
    }


    def __init__(self, method, areas=None, username=None, password=None):
        self._username, self._password = username, password
        self._method = method
        
        # Add 910 because we always want to import railway stations
        if areas is not None:
            areas += ('910',)
        self._areas = areas

    @batch('%d 10 * * mon' % random.randint(0, 59))
    def import_data(self, metadata, output):
        method, username, password = self._method, self._username, self._password
        if not method in ('http', 'ftp',):
            raise ValueError("mode must be either 'http' or 'ftp'")
        if (method == 'ftp') == (username is None or password is None):
            raise ValueError("username and password must be provided iff mode is 'ftp'")

        self._source = self._get_source()
        self._entity_types = self._get_entity_types()

        if self._method == 'http':
            self._import_from_http()
        elif self._method == 'ftp':
            self._import_from_ftp()
        
        return metadata
    
    def _connect_to_ftp(self):
        return ftplib.FTP(self.FTP_SERVER,
            self._username,
            self._password,
        )
    
    def _import_from_ftp(self):
        def data_chomper(f):
            def chomp(data):
                os.write(f, data)
            return chomp

        ftp = self._connect_to_ftp()
        
        files = {}
        
        # Get NPTG localities
        f, filename =  tempfile.mkstemp()
        ftp.cwd("/V2/NPTG/")
        ftp.retrbinary('RETR nptgcsv.zip', data_chomper(f))
        os.close(f)
        archive = zipfile.ZipFile(filename)
        if hasattr(archive, 'open'):
            f = archive.open('Localities.csv')
        else:
            f = StringIO(archive.read('Localities.csv'))
        localities = self._get_nptg(f)
        os.unlink(filename)
        
        if self._areas is None:
            f, filename = tempfile.mkstemp()
            
            try:
                ftp.cwd("/V2/complete/")
                ftp.retrbinary('RETR NaPTAN.xml', data_chomper(f))
            except ftplib.error_temp:
                ftp = self._connect_to_ftp()
                ftp.cwd("/V2/complete/")
                ftp.retrbinary('RETR NaPTAN.xml', data_chomper(f))
            
            ftp.quit()
            os.close(f)
            
            f = open(filename)
            self._import_from_pipe(f, localities)
            os.unlink(filename)
            
        else:
            for area in self._areas:
                f, filename = tempfile.mkstemp()
                files[area] = filename
            
                try:
                    ftp.cwd("/V2/%s/" % area)
                    ftp.retrbinary('RETR NaPTAN%sxml.zip' % area, data_chomper(f))
                except ftplib.error_temp:
                    ftp = self._connect_to_ftp()
                    ftp.cwd("/V2/%s/" % area)
                    ftp.retrbinary('RETR NaPTAN%sxml.zip' % area, data_chomper(f))
                os.close(f)
            
            try:
                ftp.quit()
            except ftplib.error_temp:
                pass
            
            for (area, filename) in files.items():
                archive = zipfile.ZipFile(filename)
                if hasattr(archive, 'open'):
                    f = archive.open('NaPTAN%d.xml' % int(area))
                else:
                    f = StringIO(archive.read('NaPTAN%d.xml' % int(area)))
                self._import_from_pipe(f, localities)
                archive.close()
                os.unlink(filename)

    def _import_from_http(self):
        
        # Get NPTG localities
        f, filename =  tempfile.mkstemp()
        os.close(f)
        urllib.urlretrieve(self.HTTP_NTPG_URL, filename)
        archive = zipfile.ZipFile(filename)
        if hasattr(archive, 'open'):
            f = archive.open('Localities.csv')
        else:
            f = StringIO(archive.read('Localities.csv'))
        localities = self._get_nptg(f)
        os.unlink(filename)
        
        f, filename = tempfile.mkstemp()
        os.close(f)
        urllib.urlretrieve(self.HTTP_URL, filename)
        archive = zipfile.ZipFile(filename)
        if hasattr(archive, 'open'):
            f = archive.open('NaPTAN.xml')
        else:
            f = StringIO(archive.read('NaPTAN.xml'))
        self._import_from_pipe(f, localities, areas=self._areas)
        archive.close()
        os.unlink(filename)

    def _import_from_pipe(self, pipe_r, localities, areas=None):
        parser = make_parser()
        parser.setContentHandler(NaptanContentHandler(self._entity_types, self._source, localities, areas))
        parser.parse(pipe_r)

    def _get_nptg(self, f):
        localities = {}
        csvfile = csv.reader(f)
        csvfile.next()
        for line in csvfile:
            localities[line[0]] = line[1]
        return localities

    def _get_entity_types(self):

        entity_types = {}
        category, created = EntityTypeCategory.objects.get_or_create(name='Transport')
        for stop_type in self.entity_type_definitions:
            et = self.entity_type_definitions[stop_type]
            
            try:
                entity_type = EntityType.objects.get(slug=et['slug'])
            except EntityType.DoesNotExist:
                entity_type = EntityType(slug=et['slug'])
            
            entity_type.category = category
            entity_type.uri = "http://mollyproject.org/schema/maps#%s" % et['uri-local']
            entity_type.article = et['article']
            entity_type.verbose_name = et['verbose-name']
            entity_type.verbose_name_plural = et['verbose-name-plural']
            if created:
                entity_type.show_in_nearby_list = et['nearby']
                entity_type.show_in_category_list = et['category']
            entity_type.save()

            entity_types[stop_type] = entity_type

        for stop_type, entity_type in entity_types.items():
            if entity_type.slug == 'public-transport-access-node':
                continue
            entity_type.subtype_of.add(entity_types[None])
            if stop_type.startswith('MET') and stop_type != 'MET' and entity_type.slug != self.RAIL_STATION_DEFINITION['slug']:
                entity_type.subtype_of.add(entity_types['MET'])
        

        return entity_types


    def _get_source(self):
        try:
            source = Source.objects.get(module_name="molly.providers.apps.maps.naptan")
        except Source.DoesNotExist:
            source = Source(module_name="molly.providers.apps.maps.naptan")

        source.name = "National Public Transport Access Nodes (NaPTAN) database"
        source.save()

        return source

try:
    from secrets import SECRETS
except ImportError:
    pass
else:
    if __name__ == '__main__':
        p = NaptanMapsProvider(method='ftp', username=SECRETS.journeyweb[0], password=SECRETS.journeyweb[1], areas=('340',))
        p.import_data(None, None)
