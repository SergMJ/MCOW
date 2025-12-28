# MCOW: Many Countries, One World Project

## What is MCOW?
This project has been created as a versatile tool to perform a socio-economical analysis of all of the different countries that shape our world.

- First, an ontology was created by combining data obtained through two main sources: Wikidata (a giant knowledge database that relies on huge structured data volumes got from pages such as Wikipedia) and Altoal (a RESTful API that provides and endpoint to obtain quite valuable countries information from very diverse areas).
- After standarising and integrating the data, some hierarchies were built too in order to allow a deeper study of the information.
- The next step consisted on training an embedding model (TransE) that allowed a likely future comparison and likelihood calculation between countries.
- To continue, a whole Python module that stored the embedding model and the RDF graph was developed. This is one of the key features, as it allows executing internal queries to the knowledge graph, so that loads of operations such as retrieving specific attributes or comparing tendencies can be done.
- Last, but not least, a full application was built by using Streamlit. Not only this contains the data and applies the proper logic to it's proper treatment, but also serves as a brdige between the user and the programmer by providing a Graphical User Interface (GUI) that lets the final user to take over control and extract valuable knowledge by using the tool.

## What functionalities does MCOW provide?
There are four pilars that sustain the application:
- __Tendency analysis.__ By selecting a country, the user can visualize the tendencies of all the ontology's attributes in a simple graphic. This provides a valuable and fast insight into how a certain feature has behaved through years.
- __DAFO analysis.__ This presents a simple screen in which the main strengths and weaknesses of a given country are stated, by remarking both issues such as a high public debt rate and way to go aspects like a very high sanitation access in rural environments.
- __Country direct comparison.__ The user is allowed to check out the similarities and differences of pairs of countries. This is achieved through a four levels classification amongst demographical, economical, social and territorial likelihood comparison, retrieving also which are the attributes of each class that contribute the most to their similarity level.
- __Countries querying by attributes and tendencies.__ The cherry on the top: the system finds countries that fulfills all the given conditions. These are set through filtering from a variety of attributes, whilst also being able to select how the tendency should be (ascending or descending), and even sorting the given results by how similar the countries are to a given one. This is great for identyfing threats and taking "role models" for countries that may be going through a bad time due to a specific feature.

## Libraries needed
To use this tool, the following libraries are required:
- matplotlib
- numpy
- os
- pandas
- pykeen
- pyvis
- re
- rdflib
- scikit-learn
- torch
- typing
- streamlit
- streamlit-extras
