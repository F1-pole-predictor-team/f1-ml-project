# Słownik kategoryzujący tory F1 na podstawie ich charakterystyki
# Używany do Feature Engineeringu w modelu ML

TRACK_TYPES = {
    # Tory uliczne (Street)
    'Monaco': 'street',
    'Singapore': 'street',
    'Las Vegas': 'street',
    'Baku': 'street',
    'Miami': 'street',

    # Tory bardzo szybkie (High Speed)
    'Monza': 'high_speed',
    'Spa-Francorchamps': 'high_speed',
    'Jeddah': 'high_speed',

    # Tory wymagające dużego docisku (High Aero)
    'Silverstone': 'high_aero',
    'Suzuka': 'high_aero',
    'Zandvoort': 'high_aero',
    'Barcelona': 'high_aero',
    'Qatar': 'high_aero',

    # Tory techniczne/zbalansowane
    'Bahrain': 'technical',
    'Hungaroring': 'technical',
    'Interlagos': 'technical',
    'Austin': 'technical',
    'Abu Dhabi': 'technical',
    'Imola': 'technical',
    'Montreal': 'technical',
    'Melbourne': 'technical',
    'Spielberg': 'technical',
    'Mexico': 'technical',
    'China': 'technical',
    'France': 'technical'
}