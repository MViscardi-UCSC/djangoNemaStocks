"""
hardcoded.py
Marcus Viscardi,    January 11, 2024

This file contains most of the hardcoded variables that are used throughout the project.

Editing them here should be the only place you need to change them.
"""
# Number of tubes remaining before sending refreeze email:
TUBE_REMAINING_THRESHOLD = 2

# Email all CZARs:
EMAIL_ALL_CZARS = False

# Cap colors as options for the FreezeRequestForm:
CAP_COLOR_OPTIONS = (
    ('', '---------'),
    ('pink', 'Pink'),
    ('red', 'Red'),
    ('orange', 'Orange'),
    ('yellow', 'Yellow'),
    ('green', 'Green'),
    ('blue', 'Blue'),
    ('lavender', 'Lavender'),
    ('purple', 'Purple'),
    ('white', 'White'),
    ('brown', 'Brown'),
    ('gray', 'Gray'),
    ('grey', 'Grey'),
    ('unknown', 'Unknown'),
)

# Roles options for use in the UserProfile model:
ROLE_CHOICES = [
    ('o', 'Other/Undefined'),
    ('i', 'Professor/Primary Investigator'),
    ('p', 'Postdoctoral Fellow'),
    ('c', 'Collaborator'),
    ('g', 'Graduate Student'),
    ('t', 'Technician'),
    ('u', 'Undergraduate'),
]

# This is really only used for the intial building of the database,
# if you need to add to a user's strains you can do that via the admin interface of the site!
USER_INITIALS_DICT = {
    'AC': ("Annie", "Courney", ((4012, 4100),)),
    'AP': ("Audrey", "Piatt", ((7000, 7030),)),
    'BH': ("Benjamin", "Haag", ((-1, -1),)),
    'CD': ("Christian", "Dunn", ((6101, 6200),)),
    'CN': ("Celine", "N", ((-1, -1),)),
    'CW': ("Chloe", "Wohlenberg", ((3101, 3300),)),
    'DD': ("Dori", "D", ((5101, 5104),)),
    'ES': ("Enisha", "Sehgal", ((7101, 7200),)),
    'EV': ("Evan", "Soukup", ((7031, 7100), )),
    'Giulio': ("Giulio", "unknown_Giulio", ((-1, -1),)),
    'HM': ("Heddy", "Menendez", ((1050, 1053),)),
    'Heddy': ("Heddy", "Menendez", ((1050, 1053),)),
    'HMN': ("Hannah", "Maul-Newby", ((1000, 1001),)),
    'JAA': ("Joshua", "Arribere", ((1, 999),)),
    'JA': ("Joshua", "Arribere", ((1, 999),)),
    'JK': ("John", "Kim", ((5105, 5150),
                           (5019, 5019),)),
    'JS': ("unknown_JS", "unknown_JS", ((-1, -1),)),
    'KY': ("Kevin", "Yang", ((5000, 5001),)),
    'MG': ("Marissa", "Glover", ((3000, 3027),)),
    'mg': ("Marissa", "Glover", ((3000, 3027),)),
    'MM': ("Matthew", "Modena", ((5051, 5100),)),
    'MNP': ("Makenna", "Pule", ((2100, 2150),)),
    'MJV': ("Marcus", "Viscardi", ((6000, 6100),)),
    'MV': ("Marcus", "Viscardi", ((6000, 6100),)),
    'NV': ("Nitin", "Vidyasagar", ((1151, 1168),)),
    'PM': ("Parissa", "Monem", ((1002, 1049),
                                (1054, 1100),
                                (1169, 1300))),
    'RY': ("Rayka", "Yokoo", ((4000, 4011),)),
    'SN': ("Swathi", "Nair", ((1101, 1150),)),
    'Swathi': ("Swathi", "Nair", ((1101, 1150),)),
    'TE': ("Thea", "E", ((-1, -1),)),
    
    'SS': ("Susan", "Strome (Lab)", ((-1, -1),)),
    'NB': ("Needhi", "Bhalla (Lab)", ((-1, -1),)),
    'JW': ("Jordan", "Ward (Lab)", ((-1, -1),)),
    'AZ': ("Al", "Zahler (Lab)", ((-1, -1),)),
    'LT': ("Liam", "Tran", ((-1, -1),)),
    'RT': ("Roton", "Arribere Lab", ((-1, -1),)),
    
    'XXX': ("unknown_XXX", "unknown_XXX", ((-1, -1),)),
}
