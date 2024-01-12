"""
hardcoded.py
Marcus Viscardi,    January 11, 2024

This file contains most of the hardcoded variables that are used throughout the project.

Editing them here should be the only place you need to change them.
"""

# Cap colors as options for the FreezeRequestForm:
CAP_COLOR_OPTIONS = (
    ('blue', 'Blue'),
    ('green', 'Green'),
    ('purple', 'Purple'),
    ('red', 'Red'),
    ('yellow', 'Yellow'),
)

# Roles options for use in the UserProfile model:
ROLE_CHOICES = [
    ('i', 'Professor/Primary Investigator'),
    ('p', 'Postdoctoral Fellow'),
    ('c', 'Collaborator'),
    ('g', 'Graduate Student'),
    ('t', 'Technician'),
    ('u', 'Undergraduate'),
    ('o', 'Other/Undefined'),
]