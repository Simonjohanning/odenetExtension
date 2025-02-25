import xml.etree.ElementTree as ET
import sqlite3

def create_tables(conn):
    cursor = conn.cursor()
    
    # Create LexicalEntries table
    cursor.execute('''CREATE TABLE Lexical_Entries
                      (id TEXT, Lemma_writtenForm TEXT, Lemma_partOfSpeech TEXT, Sense_id_and_synset TEXT)''')
    
    # Create Synsets table
    cursor.execute('''CREATE TABLE Synsets
                      (id TEXT, Synset_ili TEXT, Synset_partOfSpeech TEXT, Synset_definition TEXT,
                       dc_subject TEXT, dc_description TEXT, confidenceScore TEXT, Synset_example TEXT)''')
    
    # Create SenseRelation table
    cursor.execute('''CREATE TABLE Sense_Relation
                      (Sense_id_and_synset TEXT, target_and_relType TEXT)''')
    
    # Create SynsetRelation table
    cursor.execute('''CREATE TABLE Synset_Relation
                      (Synset_id TEXT, target_and_relType TEXT)''')

# def transform_relTypes(xml_file):
#     # Transformation of relTypes
#     replacements = {
#         "holo_part": "holonym",
#         "holo_substance": "holonym",
#         "holo_member": "holonym",
#         "instance_hyponym": "hyponym",
#         "mero_member": "meronym",
#         "mero_part": "meronym",
#         "mero_substance": "meronym",
#         "instance_hypernym": "hypernym"
#     }
    
#     uk_wn = open(xml_file, "r", encoding="utf-8")
#     wn_tree = ET.parse(uk_wn)
#     wn_root = wn_tree.getroot()

#     for synset in wn_root.iter("Synset"):
#         for synset_relation in synset.findall("SynsetRelation"):
#             target = synset_relation.get("target")
#             rel_type = synset_relation.get("relType")
#             if rel_type in replacements:
#                 synset_relation.set("relType", replacements[rel_type])

#     wn_tree.write('modified_relTypes_{name}.xml', encoding="utf-8")

def integrate_to_lexical_entries(conn, wn_root):
    cursor = conn.cursor()
    lex_entries_dict = {}

    for entry in wn_root.findall("./Lexicon/LexicalEntry"):
        entry_dict = {}
        entry_dict["Lemma_writtenForm"] = entry.find("./Lemma").get("writtenForm")
        entry_dict["Lemma_partOfSpeech"] = entry.find("./Lemma").get("partOfSpeech")
        senses_list = [(sense.get("id"), sense.get("synset")) for sense in entry.findall("./Sense")]
        entry_dict["Sense"] = senses_list
        lex_entries_dict[entry.get("id")] = entry_dict

    for key, value in lex_entries_dict.items():
        id_lex_entry = key
        lemma_lex_entry = value['Lemma_writtenForm']
        pos_lex_entry = value['Lemma_partOfSpeech']
        senses_list = value['Sense']
        senses_str = str(senses_list) # Has to be a string because List of tuples is not accepted by SQL

        cursor.execute('INSERT INTO Lexical_Entries (id, Lemma_writtenForm, Lemma_partOfSpeech, Sense_id_and_synset) VALUES (?, ?, ?, ?)',
                           (id_lex_entry, lemma_lex_entry, pos_lex_entry, senses_str))

def integrate_to_synsets(conn, wn_root):
    cursor = conn.cursor()
    synset_entries_dict = {}

    for entry in wn_root.findall("./Lexicon/Synset"):
        entry_dict = {}
        entry_dict["Synset_ili"] = entry.get("ili")
        entry_dict["Synset_partOfSpeech"] = entry.get("partOfSpeech")
        entry_dict["confidenceScore"] = entry.get("confidenceScore")
        entry_dict["dc_description"] = entry.get("{https://globalwordnet.github.io/schemas/dc/}description")
        entry_dict["dc_subject"] = entry.get("{https://globalwordnet.github.io/schemas/dc/}subject")
        definition = entry.find("./Definition")
        entry_dict["Synset_definition"] = definition.text if definition is not None else ""

        synset_entries_dict[entry.get("id")] = entry_dict

    for key, value in synset_entries_dict.items():
        id_synset = key
        ili_synset = value['Synset_ili']
        pos_synset = value['Synset_partOfSpeech']
        confidenceScore = value['confidenceScore']
        dc_description = value['dc_description']
        dc_subject = value['dc_subject']
        definition_synset = value['Synset_definition']

        cursor.execute('INSERT INTO Synsets (id, Synset_ili, Synset_partOfSpeech, confidenceScore, dc_description, dc_subject, Synset_definition) VALUES (?, ?, ?, ?, ?, ?, ?)',
                           (id_synset, ili_synset, pos_synset, confidenceScore, dc_description, dc_subject, definition_synset))

def integrate_to_sense_relation(conn, wn_root):
    cursor = conn.cursor()
    sense_relation_dict = {}

    for lex_entry in wn_root.findall("./Lexicon/LexicalEntry"):
        for sense in lex_entry.findall("./Sense"):
            sense_id = sense.get("id")
            synset = sense.get("synset")
            sense_relations = [(sense_rel.get("target"), sense_rel.get("relType")) for sense_rel in sense.findall("./SenseRelation")]
            sense_relation_dict[(sense_id, synset)] = sense_relations

    for key, value in sense_relation_dict.items():
        sense_id_and_synset = str(key)
        target_and_relType = str(value)  # Convert the list to a string for storage

        cursor.execute('INSERT INTO Sense_Relation (Sense_id_and_synset, target_and_relType) VALUES (?, ?)', (sense_id_and_synset, target_and_relType))

def integrate_to_synset_relation(conn, wn_root):
    cursor = conn.cursor()
    synset_relation_dict = {}

    for synset in wn_root.findall("./Lexicon/Synset"):
        synset_id = synset.get("id")
        synset_relations = [(synset_rel.get("target"), synset_rel.get("relType")) for synset_rel in synset.findall("./SynsetRelation")]
        synset_relation_dict[synset_id] = synset_relations

    for key, value in synset_relation_dict.items():
        synset_id = key
        target_and_relType = str(value)  # Convert the list to a string for storage

        cursor.execute('INSERT INTO Synset_Relation (Synset_id, target_and_relType) VALUES (?, ?)', (synset_id, target_and_relType))

if __name__ == "__main__":
    # Set user-defined parameters
    name_wn = input("Enter the name of the WordNet database: ")
    path_wn = input("Enter the path to the XML WordNet file: ")

    # Connect to SQLite database
    conn = sqlite3.connect(f'{name_wn}.db')

    # Create tables
    create_tables(conn)

    # Transform relTypes
    transform_relTypes(path_wn)

    # Parse XML WordNet file
    wn_tree = ET.parse(path_wn)
    wn_root = wn_tree.getroot()

    # Integrate data into LexicalEntries table
    integrate_to_lexical_entries(conn, wn_root)

    # Integrate data into Synsets table
    integrate_to_synsets(conn, wn_root)

    # Integrate data into SenseRelation table
    integrate_to_sense_relation(conn, wn_root)

    # Integrate data into SynsetRelation table
    integrate_to_synset_relation(conn, wn_root)

    # Commit changes and close connection
    conn.commit()
    conn.close()
