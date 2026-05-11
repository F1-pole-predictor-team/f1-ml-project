# Słownik kategoryzujący tory F1 na podstawie ich charakterystyki
# Używany do Feature Engineeringu w modelu ML

TRACK_TYPES = {
    # Tory uliczne (Street)
    'Monaco Grand Prix': 'street',
    'Singapore Grand Prix': 'street',
    'Las Vegas Grand Prix': 'street',
    'Azerbaijan Grand Prix': 'street',
    'Miami Grand Prix': 'street',

    # Tory bardzo szybkie (High Speed)
    'Italian Grand Prix': 'high_speed',
    'Belgian Grand Prix': 'high_speed',
    'Saudi Arabian Grand Prix': 'high_speed',

    # Tory wymagające dużego docisku (High Aero)
    'British Grand Prix': 'high_aero',
    'Japanese Grand Prix': 'high_aero',
    'Dutch Grand Prix': 'high_aero',
    'Spanish Grand Prix': 'high_aero',
    'Qatar Grand Prix': 'high_aero',

    # Tory techniczne/zbalansowane
    'Bahrain Grand Prix': 'technical',
    'Hungarian Grand Prix': 'technical',
    'São Paulo Grand Prix': 'technical',
    'United States Grand Prix': 'technical',
    'Abu Dhabi Grand Prix': 'technical',
    'Emilia Romagna Grand Prix': 'technical',
    'Canadian Grand Prix': 'technical',
    'Australian Grand Prix': 'technical',
    'Austrian Grand Prix': 'technical',
    'Mexico City Grand Prix': 'technical',
    'Chinese Grand Prix': 'technical',
    'French Grand Prix': 'technical'
}