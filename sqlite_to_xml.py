import sqlite3
import os
import re
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime

import dbUtils


# The input file is the exported database (.db) file of the WordNet-Editor
# For serialization, all attributes need to be strings
def generate_xml_data(connection):
    # Initialize XML content
    root = ET.Element("LexicalResource")

    words = dbUtils.extractAllWords(connection)

    # # Process Lexical Entries
    for word in words:
        lexical_entry = ET.Element("LexicalEntry")
        lexical_entry.set("id", str(word['id']))
        lemma = ET.SubElement(lexical_entry, "Lemma")
        lemma.set("writtenForm", word['writtenForm'])

        senses = dbUtils.findSynsetForWord(connection, word['writtenForm'])
        for sense in senses:
            sense_element = ET.SubElement(lexical_entry, "Sense")
            sense_element.set("id", str(word['id']) + '_' + str(sense))
            sense_element.set("synset", 'odenet-' + str(sense))
        root.append(lexical_entry)

    # # Process Synsets
    synsets = dbUtils.retrieveVisibleSynsets(connection)
    synset_relations = {}
    for currentSynset in synsets:
        synset = ET.Element("Synset")
        synset.set("id", str(currentSynset))
        root.append(synset)
        synset_relations = dbUtils.findAllRelations(connection, currentSynset)
        if(currentSynset in synset_relations):
            print("synset " + str(currentSynset) + ' is part of ' + str(currentSynset))
        preferredTerm = dbUtils.retrievePreferredTerm(connection, currentSynset)[0]
        if len(preferredTerm) > 0:
            if preferredTerm[0]:
                synset.set("dc:description", preferredTerm[0])
        # Process Synset Relations
        # process hypernyms
        # TODO some entries have more than 1 element
        for synset_relation in synset_relations['hypernym']:
            synset_relation_element = ET.Element("SynsetRelation")
            synset_relation_element.set("targets", 'odenet-' + str(synset_relation))
            synset_relation_element.set("relType", 'hypernym')
            synset.append(synset_relation_element)
        # process hyponyms
        for synset_relation in synset_relations['hyponym']:
            synset_relation_element = ET.Element("SynsetRelation")
            synset_relation_element.set("targets", 'odenet-' + str(synset_relation))
            synset_relation_element.set("relType", 'hyponym')
            synset.append(synset_relation_element)
        # process associations
        for synset_relation in synset_relations['association']:
            synset_relation_element = ET.Element("SynsetRelation")
            synset_relation_element.set("targets", 'odenet-' + str(synset_relation))
            synset_relation_element.set("relType", 'association')
            synset.append(synset_relation_element)

    # Generate XML content
    xml_content = ET.tostring(root, encoding="unicode")

    # Use BeautifulSoup to prettify XML
    soup = BeautifulSoup(xml_content, 'xml')
    pretty_xml_content = soup.prettify()

    # Remove all XML declarations
    pretty_xml_content = re.sub(r'<\?xml.*\?>\n?', '', pretty_xml_content)

    # # Add Header (Assuming the header file is in the same directory)
    # header_path = "header.xml"
    # with open(header_path, 'r') as file:
    #     wordnet_header = file.read()
    #
    # # Perform Replacements
    # wordnet_new = pretty_xml_content.replace('<LexicalResource>', wordnet_header)
    # wordnet_new = wordnet_new.replace('</LexicalResource>', '</Lexicon>\n</LexicalResource>')
    # pattern_to_replace_source = r'\ssource'
    # replacement_string_source = ' dc:source'
    # wordnet_new = re.sub(pattern_to_replace_source, replacement_string_source, wordnet_new)
    # pattern_to_replace_subject = r'\ssubject'
    # replacement_string_subject = ' dc:subject'
    # wordnet_new = re.sub(pattern_to_replace_subject, replacement_string_subject, wordnet_new)
    # pattern_to_replace_description = r'\sdescription'
    # replacement_string_description = ' dc:description'
    # wordnet_new = re.sub(pattern_to_replace_description, replacement_string_description, wordnet_new)

    # Save the XML content to a file
    output_file = f"{datetime.today().strftime('%Y%m%d')}_wordnet.xml"
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(pretty_xml_content)

    connection.close()

    print(f"XML WordNet generated and saved to {output_file}")
