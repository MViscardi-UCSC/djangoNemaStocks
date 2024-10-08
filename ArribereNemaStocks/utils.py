from pprint import pprint


def parse_strain_data(data, separator='\t', number_of_fields=6,
                      field_names=('wja', 'genotype', 'phenotype', 'source', 'description', 'additional_comments'),
                      debug=False):
    """
    Parses the pasted data and returns a list of dictionaries suitable for initializing forms.
    Assumes data is tab-separated without headers.
    """
    assert number_of_fields == len(field_names), "Number of fields must match number of field names"
    assert 'wja' in field_names, "WJA field must be present"
    parsed_data = []
    lines = data.strip().split('\n')
    for line in lines:
        fields = line.strip().split(separator)
        if debug:
            print("Fields:", fields)
        
        # Handle missing fields
        if len(fields) < number_of_fields:
            num_blank_fields_to_add = number_of_fields - len(fields)
            if debug:
                print(f"Adding {num_blank_fields_to_add} empty fields")
            fields += [''] * num_blank_fields_to_add
        # Wrap extra fields into the last field
        elif len(fields) > number_of_fields:
            extra_fields = fields[number_of_fields-1:]
            fields = fields[:number_of_fields]
            if debug:
                print(f"Extra fields: {extra_fields}")
                print(f"Non-extra fields: {fields}")
            fields[-1] = ' | '.join(extra_fields)
            if debug:
                print(f"Fields after wrapping extra fields: {fields}")
            
        # Make a dictionary of the whole thing
        fields_dict = dict(zip(field_names, fields))
        if debug:
            pprint(fields_dict)
        
        # Convert wja to integer, removing 'WJA' prefix and leading zeros
        fields_dict = {k: v.strip() for k, v in fields_dict.items()}
        fields_dict['wja'] = fields_dict.pop('wja', '').upper().lstrip('WJA').lstrip('0')
        try:
            fields_dict['wja'] = int(fields_dict['wja'])
        except ValueError:
            fields_dict['wja'] = None  # Invalid WJA number
        strain_data = fields_dict
        parsed_data.append(strain_data)
    return parsed_data
