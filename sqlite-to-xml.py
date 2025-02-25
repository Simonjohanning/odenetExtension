import sqlite3
import os
import re
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime

# The input file is the exported database (.db) file of the WordNet-Editor 

def generate_xml_data(input_file): 
    # Initialize XML content
    root = ET.Element("LexicalResource")

    connection = sqlite3.connect(input_file)
    cursor = connection.cursor()

    # Process Lexical Entries
    cursor.execute('SELECT * FROM Lexical_Entries')
    for row in cursor.fetchall():
        lexical_entry = ET.Element("LexicalEntry")
        lexical_entry.set("id", row[0])
        lemma = ET.SubElement(lexical_entry, "Lemma")
        lemma.set("writtenForm", row[1])
        lemma.set("partOfSpeech", row[2])
        senses = eval(row[3])  
        for sense in senses:
            sense_element = ET.SubElement(lexical_entry, "Sense")
            sense_element.set("id", sense[0])
            sense_element.set("synset", sense[1])
        root.append(lexical_entry)

    # Process Synsets
    cursor.execute('SELECT * FROM Synsets')
    synset_relations = {}
    for row in cursor.fetchall():
        synset = ET.Element("Synset")
        synset.set("id", row[0])
        synset.set("ili", row[1])
        synset.set("partOfSpeech", row[2])
        if row[4]:
            synset.set("dc:subject", row[4])
        if row[5]:
            synset.set("dc:description", row[5])
        if row[6]:
            synset.set("confidenceScore", row[6])
        if row[3]:
            definition = ET.SubElement(synset, "Definition")
            definition.text = row[3]
        if row[7]:
            example = ET.SubElement(synset, "Example")
            example.text = row[7]
        root.append(synset)
        synset_relations[row[0]] = []

    # Process Synset Relations
    cursor.execute('SELECT Synset_id, target_and_relType FROM Synset_Relation')
    for row in cursor.fetchall():
        synset_id, target_and_relType = row
        target_rel_list = eval(target_and_relType)
        for target, rel_type in target_rel_list:
            synset_relation = ET.Element("SynsetRelation")
            synset_relation.set("target", target)
            synset_relation.set("relType", rel_type)
            synset_relations[synset_id].append(synset_relation)

    # Add Synset Relations to Synsets
    for synset_id, synset_relations_list in synset_relations.items():
        synset_element = next((elem for elem in root.iter("Synset") if elem.get("id") == synset_id), None)
        if synset_element is not None:
            definition_element = synset_element.find("Definition")
            children = list(synset_element)  # Get all children elements
            new_children = []

            for child in children:
                new_children.append(child)
                if child == definition_element:
                    # Insert SynsetRelations immediately after the Definition element
                    new_children.extend(synset_relations_list)

            # Replace old children with new ordered children
            synset_element[:] = new_children

    # Generate XML content
    xml_content = ET.tostring(root, encoding="unicode")

    # Use BeautifulSoup to prettify XML
    soup = BeautifulSoup(xml_content, 'xml')
    pretty_xml_content = soup.prettify()

    # Remove all XML declarations
    pretty_xml_content = re.sub(r'<\?xml.*\?>\n?', '', pretty_xml_content)

    # Add Header (Assuming the header file is in the same directory)
    header_path = "header.xml"
    with open(header_path, 'r') as file:
        wordnet_header = file.read()

    # Perform Replacements
    wordnet_new = pretty_xml_content.replace('<LexicalResource>', wordnet_header)
    wordnet_new = wordnet_new.replace('</LexicalResource>', '</Lexicon>\n</LexicalResource>')
    pattern_to_replace_source = r'\ssource'
    replacement_string_source = ' dc:source'
    wordnet_new = re.sub(pattern_to_replace_source, replacement_string_source, wordnet_new)
    pattern_to_replace_subject = r'\ssubject'
    replacement_string_subject = ' dc:subject'
    wordnet_new = re.sub(pattern_to_replace_subject, replacement_string_subject, wordnet_new)
    pattern_to_replace_description = r'\sdescription'
    replacement_string_description = ' dc:description'
    wordnet_new = re.sub(pattern_to_replace_description, replacement_string_description, wordnet_new)

    # Save the XML content to a file
    output_file = f"{datetime.today().strftime('%Y%m%d')}_wordnet.xml"
    with open(output_file, 'w') as file:
        file.write(wordnet_new)

    connection.close()

    print(f"XML WordNet generated and saved to {output_file}")

# Usage - Change path here and run script afterwards
if __name__ == "__main__":
    generate_xml_data('path-to-your-db-file')
