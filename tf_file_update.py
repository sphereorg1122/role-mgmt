import ast
import csv
import re

def process_updates_from_csv(csv_file_path):
    with open(csv_file_path, mode='r', encoding='utf-8-sig') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        
        # Get the headers
        headers = csv_reader.fieldnames
        
        # Check if required columns exist
        required_columns = ["File Path", "Value", "New Value"]
        for column in required_columns:
            if column not in headers:
                print(f"Error: '{column}' column not found in the CSV file.")
                return

        # Skip the header row
        next(csv_reader)

        # Process each row
        for row in csv_reader:
            terraform_file_path = row["File Path"]
        
            if not terraform_file_path:
                print("Error: Terraform file path is empty in the CSV file.")
                continue
            
            block_type = row['Type']
            block_name = row['Name']
            attribute_name = row['Attribute']
            old_value = row['Value']
            new_value = row['New Value']
            
            # Skip if New Value is empty
            if not new_value:
                continue
            
            # Try to convert new_value to the appropriate type
            try:
                # First, try to evaluate as a Python literal
                new_value = ast.literal_eval(new_value)
            except (ValueError, SyntaxError):
                # If it's not a Python literal, keep it as a string
                pass
            
            # Special handling for boolean values
            if isinstance(new_value, str):
                lower_value = new_value.lower()
                if lower_value == 'true':
                    new_value = True
                elif lower_value == 'false':
                    new_value = False
            
            update_terraform_attribute(terraform_file_path, block_type, block_name, attribute_name, new_value)
            
            # Format new_value for consistent output
            new_value_formatted = f'"{new_value}"' if isinstance(new_value, str) and old_value.startswith('"') and old_value.endswith('"') else new_value
            
            print(f"Updated attribute '{attribute_name}' in {terraform_file_path}")
            print(f"  Old value: {old_value}")
            print(f"  New value: {new_value_formatted}")
            print()

def update_terraform_attribute(file_path, block_type, block_name, attribute_name, new_value):
    # Open the original Terraform file for reading
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Flag to track if we are inside the correct block
    inside_block = False
    updated_lines = []

    # Regex patterns to identify the block and the attribute types
    block_pattern = re.compile(rf'{block_type}\s+"{block_name}"\s+{{')
    attribute_pattern_string = re.compile(rf'\s*{attribute_name}\s*=\s*".*"')
    attribute_pattern_number = re.compile(rf'\s*{attribute_name}\s*=\s*\d+')
    attribute_pattern_boolean = re.compile(rf'\s*{attribute_name}\s*=\s*(true|false)')
    attribute_pattern_list_start = re.compile(rf'\s*{attribute_name}\s*=\s*\[.*')
    list_terminator = re.compile(r'.*\]')
    
    # Iterate through each line of the file
    for line in lines:
        # Check if we are entering the desired block (provider, resource, variable, etc.)
        if block_pattern.search(line):
            inside_block = True
            updated_lines.append(line)
            continue

        # If we are inside the block, check if the line contains the attribute to be updated
        if inside_block:
            # Check for string attribute
            if attribute_pattern_string.search(line):
                # If the attribute is a string, update its value
                updated_line = attribute_pattern_string.sub(f'  {attribute_name} = "{new_value}"', line)
                updated_lines.append(updated_line)
                continue
            # Check for number attribute
            elif attribute_pattern_number.search(line):
                # If the attribute is a number, update its value
                updated_line = attribute_pattern_number.sub(f'  {attribute_name} = {new_value}', line)
                updated_lines.append(updated_line)
                continue
            # Check for boolean attribute
            elif attribute_pattern_boolean.search(line):
                updated_line = attribute_pattern_boolean.sub(f'  {attribute_name} = {str(new_value).lower()}', line)
                updated_lines.append(updated_line)
                continue
            # Check for list attribute
            elif attribute_pattern_list_start.search(line):
                # If the attribute is a list and it spans multiple lines, handle it accordingly
                if not list_terminator.search(line):  # Check if list is multi-line
                    updated_lines.append(f'  {attribute_name} = {new_value}\n')
                    inside_block = False
                    continue
                else:
                    # Update a single-line list
                    updated_line = attribute_pattern_list_start.sub(f'  {attribute_name} = {new_value}', line)
                    updated_lines.append(updated_line)
                    continue

        # Add the line to the updated list if no changes are made
        updated_lines.append(line)

        # Check for the end of the block
        if inside_block and line.strip() == "}":
            inside_block = False

    # Write the updated lines back to the file (preserving the exact structure)
    with open(file_path, 'w') as file:
        file.writelines(updated_lines)


# --- main program starts ---

csv_file_path = 'terraform_parsed_results.csv'  # Path to your CSV file
process_updates_from_csv(csv_file_path)