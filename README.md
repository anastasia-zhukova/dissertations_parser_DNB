# Parser of DNB (Deutsche National Bibliothek) Dissertations

Acquiring domain-related data for continual pretraining of language models is often a manual and tedious task, which 
becomes even more complex when the language of interest is not English. The repository provides a script of acquiring and
parsing [300K DNB dissertations](https://www.dnb.de/dissonline) that mainly target German data. Provided a set of topic codes that can describe your domain, 
the script will parse the matching dissertations and output the paragraphs of them.

## Installation & execution
2. Install the requirements  ```pip install -r requirements.txt```
3. Run the ```parse_dissertations.py``` script. If you want to use a different config file than ```parse_config.json```, you need to modifythe main part of the script. 


## Modify the config file
The following fields can be modified in ```parse_config.json``` (or saved in a new config file):

1. ```domain_name```: a keyword that summarizes your domain (will be used when saving the output files). 
2. ```domain_codes```: The codes that represent the research areas are described in the [full](https://d-nb.info/1052700705/34) or [short](https://www.dnb.de/SharedDocs/Downloads/EN/Professionell/DDC/ddcSachgruppenDNBAb2013.pdf?__blob=publicationFile&v=4).
documents. The assigned codes in the bibliography
will typically start with these codes, so the list can't be exhaustive. The script checks if an assighed code starts with the codes provides in this list. 
3. ```exception_list```: The file above also describes which sub-codes need to be excluded/ignored from each code. If an exception code is listed for a specific domain,
it needs to be added to this list. The list can be empty.
4. ```language```: A selected language in 3-char encoding, e.g., "ger" for DE.
5. ```paragraphs_per_file```: A min number of collected paragraphs in a CSV required to trigger the file saving. 
6. ```min_chars_paragraph```: A min number of chars allowed per paragraph. Meant to filter out headlines and formulas. If you want both of them in your parsed text, set the value to 0.

## Output format 
The output is saved into ```\data``` folder as a collection of tab-delimeted csv files with parsed paragraphs.

| Column         | Description                                          |
|----------------|------------------------------------------------------|
| ```category``` | Matching domain codes of this dissertation.          |
| ```author```   | Author of the dissertation.                          |
| ```title```    | Dissertation title.                                  |
| ```url```      | URL of a parsed PDF.                                 |
| ```text```        | Paragraphs of dissertation (one paragraph per row).  |
