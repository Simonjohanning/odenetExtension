def extractAllWords(connection):
    """
    Function to extract all words from the database

    :param connection: An established connection to mySQL database
    :return: List of all words in the database as dictionary with id and writtenForm as entries
    """
    wordList = []
    cursor = connection.cursor()
    cursor.execute("SELECT id,word,normalized_word, normalized_word2 FROM term")

    # return the id and the normalized_word/normalized_word2 if they are set, otherwise return the word
    for result in cursor.fetchall():
        if result[2] is not None:
            wordList.append({'id': result[0], 'writtenForm': result[2]})
        elif result[3] is not None:
            wordList.append({'id': result[0], 'writtenForm': result[3]})
        else:
            wordList.append({'id': result[0], 'writtenForm': result[1]})
    return wordList

def convertSynsetToWord(connection, synset_id):
    """
    Function to retrieve all words (text synonyms) associated with a synset

    :param connection: An established connection to mySQL database
    :param synset_id: The id of the synset to retrieve within the db
    :return: list of all words associated with the synset
    """
    cursor = connection.cursor()
    query = "SELECT word FROM term WHERE synset_id=%s"
    cursor.execute(query, (synset_id,))
    return cursor.fetchall()

def findSynsetForWord(connection, term):
    """
    Function to list all synsets that are connected to the provided word (either as word, normalized_word or  normalized_word2)

    :param connection: An established connection to mySQL database
    :param term: The words to retrieve relevant synsets for
    :return: List of ids for synsets corresponding to the word
    """
    cursor = connection.cursor()
    query = "SELECT synset_id FROM term WHERE normalized_word=%s OR word=%s OR normalized_word2=%s"
    cursor.execute(query, (term,term, term))
    allSynsets = cursor.fetchall()
    return list(map(lambda synsetId: synsetId[0], allSynsets))

def findSynsetTerms(connection, terms):
    """
    Function to retrieve all synonyms for a list of words as text.
    Prints out all strings that are seen as synonym for any word in the provided list

    :param connection: An established connection to mySQL database
    :param terms: List of term for which the synonyms should be retrieved
    :return: void, prints out all ids and terms for the synonyms (with debug information in passing)
    """
    termIds = []
    for term in terms:
        termSynonymTerms = []
        synsets = findSynsetForWord(connection, term)
        termIds.append(synsets)
        for synset in synsets:
            termSynonymTerms.append(convertSynsetToWord(connection, synset)[0])
        print(
            "checking for term " + term + " with synsets " + str(synsets) + " and synonyms " + str(termSynonymTerms))
    print(termIds)
    print(termSynonymTerms)

#TODO check if deprecated (possible duplicate)
def sortSynsetsByRelations(connection):
    """

    :param connection: An established connection to mySQL database
    :return:
    """
    countDictionary = {}
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM synset")
        synsets = cursor.fetchall()
    for synset in synsets:
        with connection.cursor() as cursor:
            query = """
            SELECT target_synset_id
            FROM synset_link
            WHERE link_type_id = 1 AND synset_id = %s
            
            UNION
            
            SELECT id
            FROM synset_link
            WHERE link_type_id = 2 AND target_synset_id = %s;
            """
            cursor.execute(query, (synset[0],synset[0]))
            relationSynsets = cursor.fetchall()
            if len(relationSynsets) in countDictionary.keys():
                countDictionary[len(relationSynsets)].append(relationSynsets)
            else:
                countDictionary[len(relationSynsets)] = relationSynsets
    return countDictionary

def countSynsetRelations(synsetRelationDictionary):
    """
    Helper function to count the instances in a relation dictionary.

    :param synsetRelationDictionary: dictionary to count frequencies
    :return: dictionary with a sorted list of keys and the number of entries it features
    """
    sortedKeys = []
    countedDictionary = {}
    for key in synsetRelationDictionary:
        sortedKeys.append(key)
    sortedKeys.sort()
    for entry in sortedKeys:
        countedDictionary[entry] = len(synsetRelationDictionary[entry])
    return countedDictionary

# function to reduce a text to base words based on their full form as long as the attribute is set in the database.
# otherwise, the base form is kept.
def reduceToBaseWords(connection, text):
    """
    Helper function that reduces the words in the text to their base form, if it is provided in the database.
    If no reduced form exists, the original word is used. If several exist, the first is chosen.

    :param connection:  An established connection to mySQL database
    :param text: The text to reduce as string
    :return: A string representing the text with the respective words replaced by their reduced form
    """
    reducedForm = ""
    for word in text.split(" "):
        cursor = connection.cursor()
        termIdQuery = "SELECT baseform FROM word_mapping WHERE fullform='" + word+"'"
        cursor.execute(termIdQuery)
        baseform = cursor.fetchall()
        if(baseform is not None and baseform != []):
            firstTuple = baseform[0]
            reducedForm += " " + firstTuple[0]
        else:
            reducedForm += " " + word
        cursor.close()
    return reducedForm

#TODO check what exactly are the problems (circular dependencies?) and call it in other functions
def sanitizeSynsetIds(synsetArray):
    """
    Function to remove synsets that cause problems.
    Excluded sets have the ids 24248, 31993, 4762, 31833, 31487, 12489.

    :param synsetArray: the array to sanitize
    :return: A sanitized array
    """
    sanitizedArray = []
    forbiddenSynsets = [24248, 31993, 4762, 31833, 31487, 12489]
    for entry in synsetArray:
        if (entry[0] not in forbiddenSynsets):
            sanitizedArray.append(entry)
    print(sanitizedArray)
    return sanitizedArray

def reverseCountingDictionary(countedDictionary):
    """
    Function to reverse the index in a counting dictionary.
    Instead of counting how many counts each entry has, it uses the number of counts as keys and entries as values.
    This allow to list all entries that have a given count

    :param countedDictionary: dictionary with counts as values
    :return: reversed dictionary indexing the counts and lists the entities that feature this count
    """
    reversedDictionary = {0: ""}
    for dictionaryEntry in countedDictionary:
        if countedDictionary[dictionaryEntry] in reversedDictionary.keys():
            if reversedDictionary[countedDictionary[dictionaryEntry]] == "":
                reversedDictionary[countedDictionary[dictionaryEntry]] += dictionaryEntry
            else:
                reversedDictionary[countedDictionary[dictionaryEntry]] += (", " + dictionaryEntry)
        else:
            reversedDictionary[countedDictionary[dictionaryEntry]] = dictionaryEntry
    return reversedDictionary

def countCategories(wordCategoryDict):
    """
    Function to count the categories in a word-category-dictionary.
    For each category, it counts how many words are associated to it.

    :param wordCategoryDict: dictionary with words as keys and categories associated with the word as values
    :return: dictionary containing categories and the number of words associated with them in the wordCategoryDict
    """
    countedCategories = {}
    for word in wordCategoryDict:
        if len(wordCategoryDict[word]) > 0:
            for category in wordCategoryDict[word]:
                if category in countedCategories:
                    countedCategories[category] += 1
                else:
                    countedCategories[category] = 1
    return countedCategories

def printSynsetWordMappings(connection, synsets):
    """
    Helper function to print the associated word for each provided synset

    :param connection: connection to the mySQL database
    :param synsets: list of the synsets to print out
    :return: void, prints a line with the corresponding words for each synset
    """
    for synset in synsets:
        print('synset ' + str(synset) + ' corresponds to word ' + convertSynsetToWord(connection, synset)[0])

def retrieveAllSynsets(connection):
    """
    Function to retrieve all synsets from the database as ids

    :param connection: connection to the mySQL db
    :return: list of all synset ids
    """
    with connection.cursor() as cursor:
        query = "SELECT id FROM synset"
        cursor.execute(query)
        synsets = cursor.fetchall()
    return list(map(lambda synsetTuple: synsetTuple[0], synsets))

def retrieveVisibleSynsets(connection):
    """
    Function to retrieve all synsets from the database as ids

    :param connection: connection to the mySQL db
    :return: list of all synset ids
    """
    with connection.cursor() as cursor:
        query = "SELECT id FROM synset WHERE is_visible = 1"
        cursor.execute(query)
        synsets = cursor.fetchall()
    return list(map(lambda synsetTuple: synsetTuple[0], synsets))

def findShallowAssociationsAndHypernym(connection, currentSynsetId, currentPaths=[], currentPath=None, visitedNodes=None, printFlag=False, depth=1):
    """
    Function that recursively builds paths for synsets that are associations and hypernyms of a given synset

    :param depth: how deep into the graph the relations should be followed
    :param connection: An established connection to mySQL database
    :param currentSynsetId: The current node, represented as the id of the synset it corresponds to
    :param currentPaths: A growing list of all paths constructed up to this point
    :param currentPath: The path that the current synset will extend on (with each node in the path being a hypernym synset of the preceding one
    :param visitedNodes: The set of all nodes that have been considered in the recursion before. Nodes that have already been visited are skipped
    :param printFlag: Boolean debug flag that marks whether information is printed on the console or not
    :return A tuple detailing the list of paths and the visited nodes.
        currentPaths is list of all paths from the original synset id to all its (recursive) hypernyms synsets. Paths are represented as lists themselves
        visitedNodes is the set of all nodes (synsetIds) visited during function execution
    """
    if depth == 0:
        currentPath.append(currentSynsetId)
        currentPaths.append(currentPath[:])
        return currentPaths, visitedNodes
    # if printFlag:
    #     print("connection active? " + str(connection.is_connected()))
    if currentPath is None:
        currentPath = []
    if visitedNodes is None:
        visitedNodes = set()
    if printFlag:
        #print("currentState: synset: %s, currentPaths: %s currentPath: %s visitedNodes: %s" %(currentSynsetId, currentPaths, currentPath, visitedNodes))
        print("currentState: synset: %s, noPaths: %s currentPathLength: %s noVisitedNodes: %s, recursionDepth: %s" %(currentSynsetId, len(currentPaths), len(currentPath), len(visitedNodes), depth))
   # print(currentSynsetId)
    currentPath.append(currentSynsetId)
    visitedNodes.add(currentSynsetId)
    # TODO: consider using UNION ALL as duplicate entries are not an issue and UNION ALL is more performant
    with connection.cursor() as cursor:
        hypernymQuery = """
            SELECT target_synset_id 
            FROM synset_link 
            WHERE link_type_id=1 AND synset_id=%s
            UNION
            SELECT synset_id AS target_synset_id
            FROM synset_link 
            WHERE link_type_id=2 AND target_synset_id=%s
            UNION
            SELECT target_synset_id
            FROM synset_link 
            WHERE link_type_id=2 AND synset_id=%s;
        """
        cursor.execute(hypernymQuery, (currentSynsetId, currentSynsetId, currentSynsetId))
        resultIds = cursor.fetchall()
    cursor.close()
    if printFlag:
        print("retrieved hypernyms and associations: %s" %str(resultIds))
    if(resultIds is None or len(resultIds) == 0):
        currentPaths.append(currentPath[:])
    else:
        for resultId in resultIds:
            if resultId[0] not in visitedNodes:
                if printFlag:
                    print("calculating path for %s" %(resultId))
                findShallowAssociationsAndHypernym(depth - 1, connection, resultId[0], currentPaths, currentPath[:], visitedNodes, printFlag)
    return currentPaths, visitedNodes

def retrievePreferredTerm(connection, currentSynset):
    """
    Function to retrieve the preferred term for a synset

    :param connection: An established connection to mySQL database
    :param currentSynset: The synset to retrieve the preferred term for
    :return: The preferred term for the synset (if set)
    """
    cursor = connection.cursor()
    query = "SELECT synset_preferred_term FROM synset WHERE id=%s"
    cursor.execute(query, (currentSynset,))
    result = cursor.fetchall()
    cursor.close()
    return result
def findAllRelations(connection, synsetId):
    """
    Function to retrieve all relations for a given synset

    :param connection: An established connection to mySQL database
    :param synsetId: The synset to retrieve relations for
    :return: dictionary containing the relation types (hyponym, hypernym and association) as keys and a list of the respective synsets as values
    """
    relationDictionary = {'hypernym': [], 'hyponym': [], 'association': []}
    # retrieve hypernyms
    relationDictionary['hypernym'] = findRelations(connection, synsetId, [], [], options={'infoFlag': False, 'debugFlag': False, 'depth': 1, 'findHypernyms': True, 'findAssociations': False, 'findHyponyms': False})[0]
    # retrieve hyponyms
    relationDictionary['hyponym'] = findRelations(connection, synsetId, [], [], options={'infoFlag': False, 'debugFlag': False, 'depth': 1, 'findHypernyms': False, 'findAssociations': False, 'findHyponyms': True})[0]
    # retrieve associations
    relationDictionary['association'] = findRelations(connection, synsetId, [], [], options={'infoFlag': False, 'debugFlag': False, 'depth': 1, 'findHypernyms': False, 'findAssociations': True, 'findHyponyms': False})[0]
    return relationDictionary
def findRelations(connection, currentSynsetId, currentPaths, currentPath=None, visitedNodes=None, options={'infoFlag': True, 'debugFlag': False, 'depth': None, 'findHypernyms': True, 'findAssociations': True, 'findHyponyms': False}):
    """
    Function to recursively retrieve the synsets that stand in a given relation to the synset provided as currentSynsetId
    Parameters are set through the option param

    :param connection: An established connection to mySQL database
    :param currentSynsetId: The current node, represented as the id of the synset it corresponds to
    :param currentPaths: A growing list of all paths constructed up to this point
    :param currentPath: The path that the current synset will extend on (with each node in the path being in one of the provided relations to the current one)
    :param visitedNodes: The set of all nodes that have been considered in the recursion before. Nodes that have already been visited are skipped
    :param options: A dictionary containing a range of options about information printing and which relations to find
       debugFlag: Flag to indicate whether debug information should be printed out
       infoFlag: Flag to indicate whether less granulated information should be printed out
       depth: how deep into the graph the relations should be followed
       findHypernyms: Flag to indicate whether hypernyms should be retrieved for all words in the set
       findAssociations: Flag to indicate whether associations should be retrieved for all words in the set
       findHyponyms: Flag to indicate whether hyponyms should be retrieved for all words in the set
    :return A tuple detailing the list of paths and the visited nodes.
        currentPaths is list of all paths from the original synset id to all its (recursive) synsets that stand in a given relation to the word. Paths are represented as lists themselves
        visitedNodes is the set of all nodes (synsetIds) visited during function execution
    """
    if options.get('depth') is not None and options['depth'] <= 0:
            currentPath.append(currentSynsetId)
            currentPaths.append(currentPath[:])
            return currentPaths, visitedNodes
    # if printFlag:
    #     print("connection active? " + str(connection.is_connected()))
    if currentPath is None:
        currentPath = []
    if visitedNodes is None:
        visitedNodes = set()
    if options['infoFlag']:
        #print("currentState: synset: %s, currentPaths: %s currentPath: %s visitedNodes: %s" %(currentSynsetId, currentPaths, currentPath, visitedNodes))
        print("currentState: synset: %s, noPaths: %s currentPathLength: %s noVisitedNodes: %s, recursionDepth: %s" %(currentSynsetId, len(currentPaths), len(currentPath), len(visitedNodes), options['depth']))
   # print(currentSynsetId)
    currentPath.append(currentSynsetId)
    visitedNodes.add(currentSynsetId)
    if not options['findHypernyms'] and not options['findHyponyms'] and not options['findAssociations']:
        print('Empty query parameters provided!! %s' % (options))
        return
    # TODO: consider using UNION ALL as duplicate entries are not an issue and UNION ALL is more performant
    with connection.cursor() as cursor:
        relationQuery = []
        parameters = []
        if options['findHypernyms']:
            relationQuery.append("""
                  SELECT target_synset_id 
                  FROM synset_link 
                  WHERE link_type_id=1 AND synset_id=%s
              """)
            parameters.append(currentSynsetId)

        if options['findHyponyms']:
            relationQuery.append("""
                  SELECT synset_id 
                  FROM synset_link 
                  WHERE link_type_id=1 AND target_synset_id=%s
              """)
            parameters.append(currentSynsetId)

        if options['findAssociations']:
            relationQuery.append("""
                  SELECT synset_id AS target_synset_id
                  FROM synset_link 
                  WHERE link_type_id=2 AND target_synset_id=%s
              """)
            parameters.append(currentSynsetId)
            relationQuery.append("""
                  SELECT target_synset_id
                  FROM synset_link 
                  WHERE link_type_id=2 AND synset_id=%s
              """)
            parameters.append(currentSynsetId)

        if relationQuery:
            finalQuery = " UNION ".join(relationQuery)
            if options['debugFlag']:
                print(finalQuery)
                print("Parameters:", parameters)
            cursor.execute(finalQuery, parameters)
        resultIds = cursor.fetchall()
    cursor.close()
    if options['debugFlag']:
        print("retrieved relations: %s" %str(resultIds))
    if(resultIds is None or len(resultIds) == 0):
        currentPaths.append(currentPath[:])
    else:
        for resultId in resultIds:
            if resultId[0] not in visitedNodes:
                nextOptions = options.copy()
                if nextOptions.get('depth') is not None:
                    nextOptions['depth'] -= 1
                if options['debugFlag']:
                    print("calculating path for %s" %(resultId))
                findRelations(connection, resultId[0], currentPaths, currentPath[:], visitedNodes, nextOptions)
    return currentPaths, visitedNodes