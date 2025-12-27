from impl import sbc_tools as sbc
import rdflib
from rdflib import Graph, Namespace
import numpy as np
from typing import List, Tuple, Dict, Optional
import torch
from sklearn.metrics.pairwise import cosine_similarity
import os
import re

class MCOWAnalyser: 
    """
    Property analyser for the "Many Countries, One World" ontology.
    """
    
    class LocalSemanticSimilarityCalculator:
        """
        Semantic similarity calculator that uses a local MCOW ontology and queries over it.
        """
        
        def __init__(self, graph):
            """
            RDF local graph is laoded
            
            Args:
                graph: rdflib.Graph object with the MCOW ontology on it
            """
            self.graph = graph
            self.cache = {}
            self.wd = Namespace("http://www.wikidata.org/entity/")
            self.onto = Namespace("http://www.detalle-pais.es/ontology/")
        
        def execute_query(self, query):
            """Local SPARQL querying over the local graph"""
            cache_key = hash(query)
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            try:
                results = self.graph.query(query)
                result_list = list(results)
                self.cache[cache_key] = result_list
                return result_list
            except Exception as e:
                print(f"Error en consulta SPARQL: {e}")
                return []
            
        def get_least_common_subsumer(self, entity1_qid, entity2_qid):
            """
            Finds the Least Common Subsumer (LCS) between two given entities.
            """

            query = f"""
            PREFIX wd:   <http://www.wikidata.org/entity/>
            PREFIX onto: <http://www.detalle-pais.es/ontology/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT DISTINCT ?lcs ?lcsLabel WHERE {{
                wd:{entity1_qid} rdf:type ?reg1 .
                wd:{entity2_qid} rdf:type ?reg2 .
                
                FILTER(STRSTARTS(STR(?reg1), "http://www.detalle-pais.es/ontology/"))
                FILTER(STRSTARTS(STR(?reg2), "http://www.detalle-pais.es/ontology/"))
                
                ?reg1 rdfs:subClassOf* ?lcs .
                ?reg2 rdfs:subClassOf* ?lcs .
                FILTER(STRSTARTS(STR(?lcs), "http://www.detalle-pais.es/ontology/"))
                
                FILTER NOT EXISTS {{
                    ?deeper rdfs:subClassOf+ ?lcs .
                    ?reg1 rdfs:subClassOf* ?deeper .
                    ?reg2 rdfs:subClassOf* ?deeper .
                }}
                
                OPTIONAL {{ ?lcs rdfs:label ?lcsLabel }}
            }}
            ORDER BY DESC(STRLEN(STR(?lcs)))
            LIMIT 1
            """

            results = self.execute_query(query)
            if results:
                lcs_uri = str(results[0].lcs)
                label = str(results[0].lcsLabel) if results[0].lcsLabel else None
                return lcs_uri, label or lcs_uri.split("/")[-1]
            return None, None
        
        def get_depth(self, entity_qid):
            """
            Calculates the depth of a given entity.
            """
            query = f"""
            PREFIX wd:   <http://www.wikidata.org/entity/>
            PREFIX onto: <http://www.detalle-pais.es/ontology/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT (COUNT(DISTINCT ?ancestor) AS ?count) WHERE {{
                wd:{entity_qid} rdf:type ?reg .
                
                FILTER(STRSTARTS(STR(?reg), "http://www.detalle-pais.es/ontology/"))
                
                ?reg rdfs:subClassOf* ?ancestor .
                
                FILTER(STRSTARTS(STR(?ancestor), "http://www.detalle-pais.es/ontology/"))
            }}
            """

            results = self.execute_query(query)
            return int(results[0]["count"]) if results else 0
        
        def get_depth_bis(self, entity_qid):
            """
            Calculates the depth of a given entity.
            """
            if entity_qid.startswith("http"):
                lcs_uri = f"<{entity_qid}>"
            else:
                lcs_uri = f"onto:{entity_qid}"

            query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX onto: <http://www.detalle-pais.es/ontology/>

            SELECT (COUNT(DISTINCT ?ancestor) AS ?count) WHERE {{
                {lcs_uri} rdfs:subClassOf* ?ancestor .
                FILTER(STRSTARTS(STR(?ancestor), "http://www.detalle-pais.es/ontology/"))
            }}
            """

            results = self.execute_query(query)
            if results and len(results) > 0:
                return int(results[0]["count"])
            return 0
        
        def wu_palmer_similarity(self, entity1_qid, entity2_qid):
            """
            Wu & Palmer similarity = 2 * depth(lcs) / (depth(c1) + depth(c2))
            """
            lcs_qid, _ = self.get_least_common_subsumer(entity1_qid, entity2_qid)
            if not lcs_qid:
                return (None, 0.0)
            
            depth1 = self.get_depth(entity1_qid)
            depth2 = self.get_depth(entity2_qid)
            depth_lcs = self.get_depth_bis(lcs_qid)
            
            if depth1 + depth2 == 0:
                return (None, 0.0)
            
            similarity = (2.0 * depth_lcs) / (depth1 + depth2)
            lcs_qid = lcs_qid.split("/")[-1]
            
            return (lcs_qid, similarity)
        
        def get_property_values(self, country_wd_code, property_name):
            """
            Gets property-value pairs of a given entity
            """
            
            query = f"""
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            PREFIX wd: <http://www.wikidata.org/entity/>

            SELECT ?property ?value WHERE {{
                wd:{country_wd_code} ?property ?value .
                FILTER regex(str(?property), "{property_name}", "i")
            }}
            """
                        
            results = self.graph.query(query)
            
            return set([str(row.value) for row in results])
        
        def jaccard_property_similarity(self, country_one_wd_code, country_two_wd_code, property_name):
            """
            Jaccard similarity calc used on categorical attributes classification 
            (mainly, when analysing neighbours)
            Jaccard = |props(e1) ∩ props(e2)| / |props(e1) ∪ props(e2)|
            """
            props1 = self.get_property_values(country_one_wd_code, property_name)
            props2 = self.get_property_values(country_two_wd_code, property_name)
            
            if not props1 and not props2:
                return 0.0
            
            intersection = len(props1 & props2)
            union = len(props1 | props2)
            
            if union == 0:
                return 0.0
            
            return intersection / union
            

        def attribute_similarity(self, country_one, country_two, property_name):
            """
            Returns the division of the values of a given property
            """
            query = f"""                
                SELECT DISTINCT ?entityOneLabel ?entityTwoLabel ?propertyOneValue ?propertyTwoValue WHERE {{
                    wd:{country_one} onto:{property_name} ?propertyOneValue.
                    wd:{country_two} onto:{property_name} ?propertyTwoValue.
                }}

                LIMIT 1     # Avoid wasting unnecessary time looking for more triples that are not needed
            """
            property_one_value = 0
            property_two_value = 0

            result = self.graph.query(query)

            for row in result:
                property_one_value = float(row.propertyOneValue)
                property_two_value = float(row.propertyTwoValue)
            
            if max(property_one_value, property_two_value) == 0:    # If neither of them have this attribute, it will be ignored, as taking it into account
                return -1                                           # would demenish the similarity value (so a special value is returned as a flag).
                
            
            return min(property_one_value, property_two_value) / max(property_one_value, property_two_value)
    
    def __init__(self, graph):
        """
        Inicializa el analizador con un grafo de MCOW, precargando además
        el diccionario de países disponibles para las futuras consultas.
        
        Se utiliza un diccionario como caché, para almacenar los resultados
        de las consultas y así evitar volver a procesar una consulta ya ejecutada.
        
        Args:
            graph: objeto graph de rdflib con la ontología de MCOW.
            
        """
        self.graph = graph
        self.cache = {}
        self.__init_country_list()
        self._init_numerical_attributes_list()
        self.__init_country_alpha_list()
        self.local_similarity_calculator = self.LocalSemanticSimilarityCalculator(graph)
        self.model = torch.load("./impl/trained_embeddings_model.pt", weights_only=False)

        
        print(f"{len(self.graph)} triples loaded.")
    
    def __init_country_list(self):
        countries_query = """
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX wd: <http://www.wikidata.org/entity/>
                
                SELECT DISTINCT ?entity ?entityLabel WHERE {
                    ?entity rdf:type ?class ;
                    
                    ?property ?value.
                
                    # Solo entidades de Wikidata
                    FILTER(STRSTARTS(STR(?entity), STR(wd:)))
                    
                    ?entity rdfs:label ?entityLabel
                
                }
                
                ORDER BY ASC(?entityLabel)
        """

        results = self.graph.query(countries_query)
        self.countries_in_ontology = dict()

        for row in results:
            country_uri = "Q"+str(row.entity).split("Q")[-1]
            country_name = str(row.entityLabel)
            
            self.countries_in_ontology[country_name] = country_uri
        
        print(f"MCOW ontology contains {len(self.countries_in_ontology)} countries.")
    
    def __init_country_alpha_list(self):
        countries_query = """
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX wd: <http://www.wikidata.org/entity/>
                
                SELECT DISTINCT ?entity ?entityLabel ?value ?continentClass WHERE {
                    ?entity rdf:type ?continentClass ;
                    
                    ?property ?value.
                
                    # Solo entidades de Wikidata
                    FILTER(STRSTARTS(STR(?entity), STR(wd:)))
                    FILTER regex(str(?property), "alpha", "i") 
                    
                    
                    ?entity rdfs:label ?entityLabel
                
                }
                
                ORDER BY ASC(?entityLabel)
        """

        results = self.graph.query(countries_query)
        self.alpha_codes= dict()

        for row in results:
            country_name = str(row.entityLabel)
            alpha_code = str(row.value)
            continent_class = str(row.continentClass).split("/")[-1]
            
            self.alpha_codes[country_name] = (alpha_code, continent_class)
        
    def _init_numerical_attributes_list(self):
        
        numerical_attributes_query="""
            SELECT DISTINCT ?property WHERE {
                ?entity rdf:type ?class;
                ?property ?value.
                
                # Solo entidades de Wikidata
                FILTER(STRSTARTS(STR(?entity), STR(wd:)))
                FILTER(STRSTARTS(STR(?property), STR(onto:)))
                
                FILTER NOT EXISTS{
                    FILTER regex(str(?property), "classification$", "i")  # Exclude classifications.
                }
                
                FILTER NOT EXISTS{
                    FILTER regex(str(?property), "(alpha|continent|is_neighbour_of|subregion|time_zone)", "i")  # Exclude non-numeric values too, as they
                                                                                                                # make no sense when analysing tendencies.
                }
                
            }
                
            ORDER BY ASC(?property)
                    
            """

        self.numerical_attributes_list = list()
        results = self.graph.query(numerical_attributes_query)

        for row in results:
            attribute = row.property.split("/")[-1]
            self.numerical_attributes_list.append(attribute)
        
        print(f"MCOW ontology contains {len(self.numerical_attributes_list)} numerical attributes.")
    
    def get_countries_dict(self):
        return self.countries_in_ontology
    
    def get_alpha_codes_dict(self):
        return self.alpha_codes
    
    def get_numerical_attributes_list(self):
        return self.numerical_attributes_list
        
    def show_cache_keys(self):
        return self.cache.keys()
    
    def anaylse_country_values(self, country_wd_code, ratio_name, mode: Optional[str]="I"):
        """
        Calculates over the graph the countries having the desired property and following
        an increasing or decrasing tendency (both counting on an adjustment factor to avoid strict comparisons).
        
        **Args"":
        
        -> country_wd_code: the Wikidata code of the country (e.g.: Spain -> Q29).
        
        -> ratio_name: the desired attribute of the entity whose tendency is to analyse.
        
        -> mode: how the aimed tendency should look like, "I" for strictly increasing and "D"
        for strictly decreasing.
        
        **Returns"":
        
        -> Two values: "total", that shows the amount of subEntities that contains the
        desired ratio and "totalFiltered", which shows how many of the total fulfills the
        series requirement.
        
        """
        
        if mode.lower() not in ["d", "i"]:
            raise Exception("Please, introduce a valid mode (empty or 'I' for increasing values,"
                            " 'D' for decreasing ones).")

        if not country_wd_code.startswith("Q"):
            raise Exception("Please, introduce a valid Wikidata entity.")
        
        if country_wd_code not in self.countries_in_ontology.values():
            raise Exception(f"The introduced country '{country_wd_code}' code is not a valid country code or does not belong to the current ontology.")
        
        operator = "<" if mode=="I" else ">"    # Increasing -> first value < second value // Decreasing -> first value > second value
        
        dynamic_factor_condition = "(?propertyValueTwo/?propertyValueOne)*100) >= 90)" if operator == "<" else "(?propertyValueTwo/?propertyValueOne)*100) >= 110)"     # Adjust factor that allows non-strict
                                                                                                                                                                        # increasing/decreasing analysis of attributes,
                                                                                                                                                                        # as long as they also fulfill that the last and the
                                                                                                                                                                        # first values of the series meet the initial criteria
        
        cache_id = country_wd_code + "_" + ratio_name + "_" + mode
        cache_id = cache_id.lower()
        
        if cache_id not in self.cache:      # Cache checking, just in case the result is already there

            user_query = f"""
                            SELECT DISTINCT (COUNT (DISTINCT ?temporalSubentityOne) AS ?totalFiltered) ?total ?propertyValueOne ?anyoOne ?propertyValueTwo ?anyoTwo WHERE {{

                ?temporalSubentityOne rdfs:subClassOf wd:{country_wd_code};
                                    onto:{ratio_name} ?propertyValueOne;
                                    onto:anyo ?anyoOne.
            
                ?temporalSubentityTwo rdfs:subClassOf wd:{country_wd_code};
                                    onto:{ratio_name} ?propertyValueTwo;
                                    onto:anyo ?anyoTwo.

                {{
                    SELECT ?anyo (COUNT (DISTINCT ?temporalSubentity) AS ?total) WHERE {{
                        ?temporalSubentity rdfs:subClassOf wd:{country_wd_code};
                                        onto:{ratio_name} ?propertyValue;
                                        onto:anyo ?anyo.
                    }}
                }}


                FILTER(?anyoTwo > ?anyoOne && (?propertyValueOne {operator} ?propertyValueTwo || ({dynamic_factor_condition})
            
                FILTER NOT EXISTS {{
                    ?temporalSubentityPrev rdfs:subClassOf wd:{country_wd_code};
                                        onto:{ratio_name} ?propertyValuePrev;
                                        onto:anyo ?anyoPrev.
                    FILTER(?anyoPrev > ?anyoOne && ?anyoPrev < ?anyoTwo)  # Makes sure no year exists between the pair
                }}
            }}


                """
            
            first_val = ""
            last_val = ""
            
            first_value_query = f"""
                SELECT DISTINCT ?propertyValue WHERE {{
                    ?temporalSubentity rdfs:subClassOf wd:{country_wd_code};
                    onto:{ratio_name} ?propertyValue;
                    onto:anyo ?anyo.
                }}
            
                ORDER BY ASC(?anyo)
                LIMIT 1"""
            
            results = self.graph.query(first_value_query)
            for row in results:
                first_val = row.propertyValue
            
            last_value_query = f"""
                SELECT DISTINCT ?propertyValue WHERE {{
                    ?temporalSubentity rdfs:subClassOf wd:{country_wd_code};
                    onto:{ratio_name} ?propertyValue;
                    onto:anyo ?anyo.
                }}
            
                ORDER BY DESC(?anyo)
                LIMIT 1"""
            
            results = self.graph.query(last_value_query)
            for row in results:
                last_val = row.propertyValue
                
            print(f"First val: {first_val} Last val {last_val}")
            
            if (operator == "<" and first_val<last_val) or (operator == ">" and first_val>last_val):    # If, even with the factor adjustement corrections the original
                                                                                                        # criteria is met, the value is returned.
                results = self.graph.query(user_query)
                print(country_wd_code)
                for row in results:
                    print(row.total, row.totalFiltered)
                    result_dict = {"total":row.total, "totalFiltered":row.totalFiltered}
                    self.cache[cache_id] = result_dict
                    
                    return result_dict   # Just a single result, returned inmediately
            
            return dict()       # Else, an empty dictionary is returned, as the condition has not been met.
        
        else:   # Already processed query; better avoid executing it again
            
            return self.cache[cache_id]
        
    
    def analyse_graph_values(self, ratio_name, mode: Optional[str]="I"):
        """
        Calls "analyse_country_values" for each country in the graph, returning the WD code
        and the country name of those who fulfill the request.
        
        **Args"":
        
        -> ratio_name: the desired attribute of the entity whose tendency is to analyse.
        
        -> mode: how the aimed tendency should look like, "I" for strictly increasing and "D"
        for strictly decreasing.
        
        **Returns"":
        
        -> A dictionary containing the Wikidata key and the name of the countries that
        fulfill the requirements.
        
        """
        
        if mode.lower() not in ["d", "i"]:
            raise Exception("Please, introduce a valid mode (empty or 'I' for increasing values,"
                            " 'D' for decreasing ones).")
        
        if ratio_name not in self.numerical_attributes_list:
            raise Exception("The introduced ratio is mispelled or does not belong to the ontology.")
        
        result_dict = dict()

        for country_name, country_id in self.countries_in_ontology.items():
            result = self.anaylse_country_values(country_id, ratio_name, mode)
            
            print(result)
            
            if "total" in result and "totalFiltered" in result and result["totalFiltered"]:
                total = int(result["total"])
                totalFiltered = int(result["totalFiltered"])
                
                if(totalFiltered==total-1):     # If the tendency is absolutely strict, the country is
                                                # added to the returning dictionary.
                    result_dict[country_name] = country_id

        return result_dict
    
    
    def multi_analyse_graph_values(self, ratio_dict):
        """
        Calls "analyse_country_values" for each country in the graph, returning the WD code
        and the country name of those who fulfill each single request, and then doing set intersection
        to return the countries that matches all of them.
        
        **Args"":
        
        -> ratio_dict: a dictionary of pairs ratio-mode with the metrics that want to be checked out
        (e.g.: {"inflation_rate":"D", "natality_rate":"I"})
        
        **Returns"":
        
        -> A dictionary containing the Wikidata key and the name of the countries that
        fulfill ALL the requirements (through set intersection).
        
        """
        
        res_dict = dict()
        res_set = set()
        
        for ratio, mode in ratio_dict.items():
            
            if ratio not in self.numerical_attributes_list:
                raise Exception("The introduced ratio is mispelled or does not belong to the ontology.")
            
            called_dict = self.analyse_graph_values(ratio, mode)
            called_set = set([k for k,v in called_dict.items()])
            
            print(called_dict)
            
            if len(res_dict) == 0:
                res_dict = called_dict.copy()
                res_set = called_set
            else:
                res_set = res_set.intersection(called_set)
                res_dict = {k:v for k,v in res_dict.items() if k in res_set}
                print(res_dict)
        
        return res_dict
    
    
    def getDAFOAnalysis(self, country_wd_code):
        """
        Computes an analysis of the given country and returns a dictionary with the strengths and
        the weaknesses of it.
                
        **Args"":
        
        -> country_wd_code: the Wikidata code of the country (e.g.: Spain -> Q29).
        
        **Returns"":
        
        -> A dictionary whose keys are "strengths"/"weaknesses" and the values another dictionary
        whose keys are the analysed classification and whose value is to which one they belong
        (e.g.: {
                "strengths":{"mortality_classification":"very_low_mortality"}, 
                "weaknesses": {"natality_classification":"very_low_natality"}
                }
        ).
        """
        
        dafoQuery = f"""
        
        SELECT DISTINCT ?propertyName ?propertyValue WHERE {{
          wd:{country_wd_code} ?propertyName ?propertyValue.
          FILTER(STRENDS(STR(?propertyName), "classification"))
        }}
        """
        
        if country_wd_code not in self.countries_in_ontology.values():
            raise Exception(f"The introduced country code '{country_wd_code}' is not a valid country code or does not belong to the current ontology.")
        
        cache_id = "dafo_" + country_wd_code
        
        if cache_id not in self.cache:
        
            concepts_set_one = ["natality", "rural_access", "urban_access"]     # Concepts that are better the highest possible
            concepts_set_two = ["unscolarization", "unemployment_rate", "mortality", "inflation_rate", "debt"]   # Concepts that are better the lowest possible
            strengths_list = ["age_balanced_population"]
            weaknesses_list = ["extremely_elder_population", "majorly_elder_population", "extremely_underaged_population"]
            
            for concept in concepts_set_one:
                strengths_list.append("high_" + concept)
                strengths_list.append("very_high_" + concept)
                weaknesses_list.append("low_" + concept)
                weaknesses_list.append("very_low_" + concept)

            for concept in concepts_set_two:
                strengths_list.append("low_" + concept)
                strengths_list.append("very_low_" + concept)
                weaknesses_list.append("high_" + concept)
                weaknesses_list.append("very_high_" + concept)
                
            result_strengths = dict()
            result_weaknesses = dict()

            results = self.graph.query(dafoQuery)
            
            for row in results:
                propertyName = str(row.propertyName)
                propertyValue = str(row.propertyValue)
                
                if propertyValue in strengths_list:
                    result_strengths[propertyName] = propertyValue
                    
                elif propertyValue in weaknesses_list:
                    result_weaknesses[propertyName] = propertyValue
            
            res_dict = {"strengths": result_strengths, "weaknesses": result_weaknesses}
            
            self.cache[cache_id] = res_dict
            
            return res_dict
        
        else:
            return self.cache[cache_id]
    
    
    def getAttributesSimilarity(self, country_one_wd_code, country_two_wd_code, attribute_set_chosen):
        """
        Computes the similarity between two given countries by certain attributes in function of
        the chosen set, being it:

            -> Demographic (D): analyses population based aspects (natality rate, life expectancy...)
            -> Economical (E): studies economical properties (public debt rate, inflation incurred...)        
            -> Social (S): takes on social issues (medical coverage, education...)
            -> Territorial (T): computes structural similarity and analyses some territorial attributes (neighbours, area extension)
                
        **Args"":
        
        -> country_one_wd_code: the Wikidata code of the first country (e.g.: Spain -> Q29).
        
        -> country_two_wd_code: the Wikidata code of the second country (e.g.: Portugal -> Q45).
        
        -> attribute_set_chosen: code of the attributes to be analysed
        
        **Returns"":
        
        -> A float (0, 1) indicating the similarity of the given countries

        """
        
        if country_one_wd_code not in self.countries_in_ontology.values():
            raise Exception(f"The introduced country code '{country_one_wd_code}' is not a valid country code or does not belong to the current ontology.")
        
        if country_two_wd_code not in self.countries_in_ontology.values():
            raise Exception(f"The introduced country code '{country_two_wd_code}' is not a valid country code or does not belong to the current ontology.")
        
        if attribute_set_chosen.lower() not in ["d", "e", "s", "t"]:
            raise Exception("Please, introduce a valid mode ('D' for demographic, 'E' for economical,"
                            " 'S' for social or 'T' for territorial analysis).")
        
        social_attributes = ["rural_sanitation_access", "urban_sanitation_access", "unemployment_rate", "youth_unscolarized_percentage"]
        demographic_attributes = ["average_children", "life_expectancy", "mortality_rate", "natality_rate", "population", "population_growth_rate", "0_to_14_years", "15_to_64_years", "65_years_and_over"]
        economic_attributes = ["economical_growth_rate", "inflation_rate", "public_debt_rate"]
        territorial_attributes = ["area_int", "is_neighbour_of"]    # Still need continent, subregion and time_zone, but these will be evaluated through graph hierarchies
        
        option = attribute_set_chosen.lower()
        
        if option == "t":
            
            lcs, palmer_similarity = self.local_similarity_calculator.wu_palmer_similarity(country_one_wd_code, country_two_wd_code)
            scalar_values_similarity = self.local_similarity_calculator.attribute_similarity(country_one_wd_code, country_two_wd_code, territorial_attributes[0])
            categorical_values_similarity = self.local_similarity_calculator.jaccard_property_similarity(country_one_wd_code, country_two_wd_code, territorial_attributes[1])
            
            computed_value = 0.75*palmer_similarity + 0.125*scalar_values_similarity + 0.125*categorical_values_similarity
            
            return {"total": computed_value, "palmer_sim": palmer_similarity, "lcs": lcs, "scalar": scalar_values_similarity, "jaccard": categorical_values_similarity}
        
        else:
            
            chosen_numerical_set = list()
            
            if option == "d":
                chosen_numerical_set = demographic_attributes
            elif option == "e":
                chosen_numerical_set = economic_attributes
            else:
                chosen_numerical_set = social_attributes
                
            computed_value = 0
            output_values = dict()
            selected_attrs = 0
            
            for attr in chosen_numerical_set:
                new_value = self.local_similarity_calculator.attribute_similarity(country_one_wd_code, country_two_wd_code, attr)
                if new_value == -1:
                    continue
                output_values[attr] = new_value
                computed_value += new_value
                selected_attrs += 1
            
            if selected_attrs == 0:                                 # There are some cases (like Armenia) that do not have any of the attributes, so this case would only
                if country_one_wd_code == country_two_wd_code:      # take place when comparing countries like it (or even the country and itself).
                    computed_value = 1                                                       
                else:
                    computed_value = 0
            
            else:
                computed_value /= selected_attrs
                
            return {"total": computed_value, "values_dict": output_values}
        
    
    def getTemporalEntityData(self, country_wd_code):
        """
        Analyses the temporal values of a given entity and returns the value of each attribute in each of those moments.
                
        **Args"":
        
        -> country_wd_code: the Wikidata code of the first country (e.g.: Spain -> Q29).
        
        **Returns"":
        
        -> A dictionary whose keys are the names of the attributes and whose values are lists of pairs (year, value).

        """
        
        if country_wd_code not in self.countries_in_ontology.values():
            raise Exception(f"The introduced country code '{country_wd_code}' is not a valid country code or does not belong to the current ontology.")

        user_query = f"""
                        SELECT ?temporalSubentity ?property ?propertyValue ?anyo WHERE {{

                            ?temporalSubentity rdfs:subClassOf wd:{country_wd_code};
                                            ?property ?propertyValue;
                                            onto:year ?anyo.
                                            
                            FILTER(STRSTARTS(STR(?property), STR(onto:)))
                            FILTER NOT EXISTS{{
                                FILTER regex(str(?property), "year", "i")  # Exclude year values.
                            }}
                        }}


                        """
                        
        res = self.graph.query(user_query)

        temporal_entity_data_dict = dict()

        for row in res:
            prop = str(row.property).split("/")[-1]
            year = int(row.anyo)
            
            prop_value = None
            prop_value_str = str(row.propertyValue)
            
            if re.search("[0-9]+\.[0-9]+", prop_value_str):    # It is a float number
                prop_value = float(prop_value_str)
                
            elif re.search("[0-9]+", prop_value_str):
                prop_value = int(prop_value_str)
            
            else:
                prop_value = prop_value_str
                
            if prop not in temporal_entity_data_dict:
                temporal_entity_data_dict[prop]= list()

            temporal_entity_data_dict[prop].append((year, prop_value))
            
        return temporal_entity_data_dict
    
    
    def obtener_embedding_entidad(model, entity_name: str, entity_to_id: Dict) -> np.ndarray:
        """
        Obtiene el vector embedding de una entidad
        """
        if entity_name not in entity_to_id:
            raise ValueError(f"Entidad '{entity_name}' no encontrada en el grafo")

        entity_id = entity_to_id[entity_name]
        embedding = model.entity_representations[0](
            torch.tensor([entity_id])
        ).detach().numpy()[0]

        return embedding

    def calcular_similitudes_paises(result, paises: List[str]):
        """
        Calcula la matriz de similitud entre países usando embeddings
        """
        model = result.model
        entity_to_id = result.training.entity_to_id

        print("\n" + "=" * 70)
        print("CÁLCULO DE SIMILITUDES CON EMBEDDINGS")
        print("=" * 70)

        # Obtener embeddings de todas las países
        embeddings = []
        paises_validos = []

        for pais in paises:
            try:
                emb = obtener_embedding_entidad(model, pais, entity_to_id)
                embeddings.append(emb)
                paises_validos.append(pais)
            except ValueError as e:
                print(f"⚠ {e}")

        embeddings = np.array(embeddings)

        # Calcular matriz de similitud coseno
        sim_matrix = cosine_similarity(embeddings)

        # Mostrar resultados
        print(f"\nMatriz de similitud (coseno) entre {len(paises_validos)} paises:\n")
        print(f"{'':20}", end='')
        for p in paises_validos:
            print(f"{p:12}", end='')
        print()

        for i, p1 in enumerate(paises_validos):
            print(f"{p1:20}", end='')
            for j, p2 in enumerate(paises_validos):
                print(f"{sim_matrix[i][j]:12.4f}", end='')
            print()

        return sim_matrix, paises_validos, embeddings

    def encontrar_paises_similares(result, pais_query: str, top_k: int = 3):
        """
        Encuentra los k países más similares a un país dado
        """
        model = result.model
        entity_to_id = result.training.entity_to_id
        id_to_entity = {v: k for k, v in entity_to_id.items()}

        # Obtener todas los países del grafo
        todos_paises = [ent for ent in entity_to_id.keys()
                        if ent not in ['type', 'Movie', 'director', 'actor', 'genre',
                                        'name', 'label', 'SciFi', 'Drama', 'Action',
                                        'Thriller', 'Romance', 'Crime']]

        # Obtener embedding de el país query
        try:
            query_emb = obtener_embedding_entidad(model, pais_query, entity_to_id)
        except ValueError as e:
            print(f"Error: {e}")
            return

        # Calcular similitud con todas los países
        similitudes = []
        for pais in todos_paises:
            if pais != pais_query:
                try:
                    emb = obtener_embedding_entidad(model, pais, entity_to_id)
                    sim = cosine_similarity([query_emb], [emb])[0][0]
                    similitudes.append((pais, sim))
                except:
                    pass

        # Ordenar por similitud
        similitudes.sort(key=lambda x: x[1], reverse=True)

        print(f"\n{'=' * 70}")
        print(f"Top {top_k} paises similares a '{pais_query}':")
        print(f"{'=' * 70}")
        for i, (pais, sim) in enumerate(similitudes[:top_k], 1):
            print(f"{i}. {pais:20} (similitud: {sim:.4f})")
            