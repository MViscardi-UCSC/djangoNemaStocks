from pprint import pprint


def parse_strain_data(data, separator='\t'):
    """
    Parses the pasted data and returns a list of dictionaries suitable for initializing forms.
    Assumes data is tab-separated without headers.
    """
    # print(f"Input Data:\n\n{data}\n")
    parsed_data = []
    lines = data.strip().split('\n')
    for line in lines:
        # print(f"Line:\n\n{line}")
        fields = line.strip().split(separator, 5)  # 5 splits makes 6 fields?
        # Handle missing fields
        fields += [''] * (6 - len(fields))
        # Wrap extra fields into the last field
        fields[-1] = separator.join(fields[5:])
        # print(f"Fields:\n\n{fields}")
        wja_str, genotype, phenotype, source, description, additional_comments = fields
        # Convert wja to integer, removing 'WJA' prefix and leading zeros
        wja_str = wja_str.strip().lstrip('WJA').lstrip('0')
        try:
            wja = int(wja_str)
        except ValueError:
            wja = None  # Invalid WJA number
        strain_data = {
            'wja': wja,
            'genotype': genotype.strip(),
            'phenotype': phenotype.strip(),
            'source': source.strip(),
            'description': description.strip(),
            'additional_comments': additional_comments.strip(),
        }
        # pprint(strain_data)
        parsed_data.append(strain_data)
    return parsed_data
