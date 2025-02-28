A number of adaptations had to be made in order to make the scripts used with the original openThesaurus data compatible with the more current dumps.
The original script is retained with the suffix _old. These changes are documented in this file.
For this, it was important that the original data for ilis and POS as well as the relations were preserved.
New relations were added as they were available in the current OpenThesaurus data.

## Original db structure
The original database featured four tables with the names Lexical_Entries, Synsets, Sense_Relation and Synset_Relation. The tables were structured as follows:

The structure of the tables is as follows:

### table lexical_entries
 - id: TEXT
 - Lemma_writtenForm: TEXT
 - Lemma_partOfSpeech: TEXT
 - Sense_id_and_synset: TEXT

### table synsets
 - id: TEXT
 - Synset_ili: TEXT
 - Synset_partOfSpeech: TEXT
 - Synset_definition: TEXT
 - dc_subject: TEXT
 - dc_description: TEXT
 - confidenceScore: TEXT
 - Synset_example: TEXT

### table sense_relation
- Sense_id_and_synset: TEXT
- target_and_relType: TEXT

### table synset_relation
- Synset_id: TEXT
- target_and_relType: TEXT

## Current dump structure
The current dump features a range of tables with the following structure:

### table category
- id: bigint(20)
- version: bigint(20)
- category_name: varchar(255)
- is_disabled: bit(1)
  
Description: Topics; each synset can be in any number of categories.

### table category_link
- id: bigint(20)
- version: bigint(20)
- category_id: bigint(20)
- synset_id: bigint(20)

Description: Table to connect 'synset' and 'category' tables.

### table language
- id: bigint(20)
- version: bigint(20)
- long_form: varchar(255)
- short_form: varchar(255)
- is_disabled: bit(1)

Description: Brief table to identify language tags. id=1: English/en, id=2: German/de.

### table link_type
- id: bigint(20)
- version: bigint(20)
- link_name: varchar(255)
- other_direction_link_name: varchar(255)
- verb_name: varchar(255)

Description: Describes the type of link: id=1: hyper/hyponym, id=2: association.

### table tag
- id: bigint(20)
- version: bigint(20)
- color: varchar(255)
- created: datetime
- created_by: varchar(255)
- name: varchar(255)
- short_name: varchar(255)
- is_visible: bit(1)

Description: Table for managing tags.

### table term_tag
- term_tags_id: bigint(20)
- tag_id: bigint(20)

Description: Simple key linkage table between term and tag.

### table synset
- id: bigint(20)
- version: bigint(20)
- evaluation: int(11)
- is_visible: bit(1)
- original_id: int(11)
- preferred_category_id: bigint(20)
- section_id: bigint(20)
- source_id: bigint(20)
- synset_preferred_term: varchar(255)

Description: Table for listing the synonym set. Each concept corresponds to a row, and terms that share the same synset_id belong to the same synset. Concepts are never deleted but marked as not visible by setting the is_visible column to 0.

### table synset_link
- id: bigint(20)
- version: bigint(20)
- evaluation_status: int(11)
- fact_count: int(11)
- link_type_id: bigint(20)
- synset_id: bigint(20)
- target_synset_id: bigint(20)

Description: Describes the connections between synsets (e.g., hypernym/hyponym). Linked to the link_type table.

### table term
- id: bigint(20)
- version: bigint(20)
- language_id: bigint(20)
- level_id: bigint(20)
- normalized_word: varchar(255)
- original_id: int(11)
- synset_id: bigint(20)
- user_comment: varchar(400)
- word: varchar(255)
- normalized_word2: varchar(255)

Description: Describes the individual words used in synsets. Words with more than one meaning have as many entries in this table as they have meanings. Words are not deleted in this table, so always check the is_visible column by joining with the synset table.

### table term_level
- id: bigint(20)
- version: bigint(20)
- level_name: varchar(255)
- short_level_name: var


## Mapping
Mapping the original script to the sql database requires a number of assumptions.

### Original Script 

The original script and the respective structure in the xml file organize the data in lexical entries (ElementTree Elements and SubElements), 
which consist of their _id_, the (single) _lemma_ and (multiple) _sense_ elements, which in turn contain the
_writtenForm_ and _partOfSpeech_ (for _lemma_) and _id_ and _synset_ entries for each individual _sense_. 

An example is given below, taken from the [OdeNet: Compiling a German Wordnet from other Resources](https://melaniesiegel.de/publications/2021_Siegel_Bond_GWC.pdf) article:

```xml
<LexicalEntry id="w33556">
    <Lemma writtenForm="Beweglichkeit"
        partOfSpeech="n"/>
        <Sense id="w33556_8203-n"
        synset="odenet-8203-n"/>
        <Sense id="w33556_9784-n"
        synset="odenet-9784-n"/>
        <Sense id="w33556_11420-n"
        synset="odenet-11420-n"/>
        <Sense id="w33556_19087-n"
        synset="odenet-19087-n"/>
</LexicalEntry>
```

The synsets are then organized in a similar fashion, with the _id_, _ili_, _partOfSpeech_, _dc:subject_, _dc:description_, _confidenceScore_ and _example_ entries, as well as _definition_ as SubElement.
In a reduced example (see [OdeNet article](https://melaniesiegel.de/publications/2021_Siegel_Bond_GWC.pdf)), the synsets are structured as follows:

```xml
<Synset id="de-9784-n"
    ili="i62097"
    partOfSpeech="n"
    dc:description="the quality of moving
    freely">
    <SynsetRelation
    targets=’odenet-23172-n’
    relType=’hypernym’/>
</Synset>
```

Relations are extracted from the Synset_Relation table as Elements with the _target_ and _relType_ entries.
For each synset relation, the elements with the respective ids are searched and their definition as well as children are found and the list of children is extended

Finally, the ElementTree is converted to string and cast to xml. 

### Script modification 

The script is changed as follows to reflect the different structure of the modern sql database:

#### Lexical Entries
Lexical entries are constructed by taking words from the term table. 
If the word is normalized (normalized_word or normalized_word2 is set), this form is used as writtenForm of the lemma, otherwise the original word is chosen.
Current, no PoS is set.

For the senses, each synset is extracted through the synset_id entries;  
the id for the sense is created by composing the id of the word with the id of the synset, separated by an underscore.

#### Synsets
Synsets are constructed by taking the synset_id from the synset table, with the id being integrated directly.
Invisible synsets (is_visible=0) are not ignored in this.
Their _ili_ and _partOfSpeech_ are ignored, with _dc:description_ being set to the _synset_preferred_term_, if set.

Finally, SynsetRelations are constructed by quering the synset_link table. 
Through the link_type_id, the synset_id and the target_synset_id, the relation is constructed and recorded whether this is a hypernym, hyponym or association relation.


## Things not integrated
For Lexical entries, the PoS is not yet integrated. This will be done by some nlp library at a later point.
For Synsets, the same goes for the PoS and _ili_, which will be taken from the .xml data of the original dump. 