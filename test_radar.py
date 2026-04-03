import opensky_api

flights = [
    'SC8007',   # 산동항공
    'SC4619',   # 산동항공
    'LJ766',    # 진에어
    '7C192',    # 제주항공
    'ET673',    # 에티오피아항공
    'KE714',    # 대한항공
    'AF5377',   # 에어프랑스 (코드쉐어 -> KE714)
    'JL5253',   # 일본항공 (코드쉐어 -> KE714)
    'AM6707',   # 아에로멕시코 (코드쉐어 -> KE714)
    'DL7902',   # 델타항공 (코드쉐어 -> KE714)
]

for f in flights:
    icao = opensky_api.iata_to_icao_callsign(f)
    r = opensky_api.get_target_flight_status(f)
    if r:
        print(f"  [OK]   {f:8s} -> {icao:10s} | lat={r['lat']:.2f} lon={r['lon']:.2f} 고도={int(r['alt'])}m")
    else:
        print(f"  [MISS] {f:8s} -> {icao:10s} | 신호 없음")
