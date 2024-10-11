import csv
import re

def read_attribute_from_file(file_path, type_value, name, attribute):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            # Create a pattern to match Type, Name, and Attribute
            pattern = rf'{re.escape(type_value)}\s+"{re.escape(name)}"\s+{{[^}}]*{re.escape(attribute)}\s*=\s*([^,\n]+)'
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()  # Return the captured value
        return None  # Return None if no match is found
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
    return None

def process_csv(input_csv_file, output_csv_file):
    results = []
    
    with open(input_csv_file, 'r') as file:
        csv_reader = csv.DictReader(file)
        
        for row in csv_reader:
            new_value = row['New Value'].strip()
            
            # Skip rows where 'New Value' is empty
            if not new_value:
                continue
            
            file_path = row['File Path']
            type_value = row['Type']
            name = row['Name']
            attribute = row['Attribute']
            
            current_value = read_attribute_from_file(file_path, type_value, name, attribute)
            
            if current_value is not None:
                print(f"File: {file_path}")
                print(f"Type: {type_value}")
                print(f"Name: {name}")
                print(f"Attribute: {attribute}")
                print(f"Current value in .tf file: {current_value}")
                print(f"New value as specified in the CSV file: {new_value}")
                
                if current_value == new_value:
                    result = "The values are the same"
                    print("\033[32m" + result + "\033[0m")  # Green text
                else:
                    result = "The values are different"
                    print("\033[1;31m" + result + "\033[0m")  # Red text
                
                print("-" * 40)  # Separator for readability
                
                results.append({
                    'File Path': file_path,
                    'Type': type_value,
                    'Name': name,
                    'Attribute': attribute,
                    'Current Value in .tf File': current_value,
                    'New Value as Specified in the CSV File': new_value,
                    'Result': result
                })
            else:
                print(f"Attribute not found or error occurred for:")
                print(f"File: {file_path}, Type: {type_value}, Name: {name}, Attribute: {attribute}")
                print("-" * 40)  # Separator for readability

    # Write results to output CSV file
    with open(output_csv_file, 'w', newline='') as file:
        fieldnames = ['File Path', 'Type', 'Name', 'Attribute', 'Current Value in .tf File', 
                      'New Value as Specified in the CSV File', 'Result']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            writer.writerow(result)

    print(f"Results have been written to {output_csv_file}")

# Usage
input_csv_file = 'terraform_parsed_results.csv'
output_csv_file = 'terraform_comparison_summary.csv'
process_csv(input_csv_file, output_csv_file)
