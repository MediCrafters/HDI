import requests
import re
# Set up your UMLS API key
API_KEY = '46673b43-5ec5-49f1-b6a7-ca0982303727'  # Replace this with your actual UMLS API key

# Function to get Ticket Granting Ticket (TGT)
def get_umls_auth_token(api_key):
    auth_endpoint = 'https://utslogin.nlm.nih.gov/cas/v1/api-key'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = f'apikey={api_key}'

    response = requests.post(auth_endpoint, headers=headers, data=data)
    if response.status_code == 201:
        # Extract TGT from the Location header
        tgt = response.headers['location']
        return tgt
    else:
        raise Exception('Error retrieving UMLS authentication token: ' + response.text)

# Function to get a Service Ticket (ST) using TGT
def get_service_ticket(tgt):
    service = 'http://umlsks.nlm.nih.gov'
    response = requests.post(tgt, data={'service': service})
    if response.status_code == 200:
        return response.text
    else:
        raise Exception('Error retrieving UMLS service ticket: ' + response.text)
print(get_umls_auth_token(API_KEY))
get_service_ticket(get_umls_auth_token(API_KEY))

# Function to search for the CUI of a medical term
def search_umls_cui(term, ticket):
    search_endpoint = 'https://uts-ws.nlm.nih.gov/rest/search/current'
    params = {
        'string': term,
        'ticket': ticket,
        'searchType': 'exact'  # Using 'exact' to get the best match
    }

    response = requests.get(search_endpoint, params=params)
    if response.status_code == 200:
        results = response.json()
        if results['result']['results']:
            # Extract the first CUI found
            return results['result']['results'][0]['ui']
        else:
            print("No CUI found for the term.")
            return None
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

def get_umls_definitions(cui, ticket):
    definition_endpoint = f'https://uts-ws.nlm.nih.gov/rest/content/current/CUI/{cui}/definitions'
    params = {'ticket': ticket}

    response = requests.get(definition_endpoint, params=params)
    if response.status_code == 200:
        definitions = response.json()
        if definitions['result']:
            return [item['value'] for item in definitions['result']]
        else:
            print("No definitions found for the CUI.")
            return None
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

def get_medical_term_definitions(term, preferred_language='english'):
    try:
        # Step 1: Get the authentication token (TGT)
        tgt = get_umls_auth_token(API_KEY)

        # Step 2: Get a service ticket (ST)
        ticket = get_service_ticket(tgt)

        # Step 3: Search for the CUI of the term
        cui = search_umls_cui(term, ticket)

        if cui:
            print(f"Found CUI: {cui}")

            # Step 4: Get definitions using the CUI
            ticket = get_service_ticket(tgt)  # Refresh the ticket for each API call
            definitions = get_umls_definitions(cui, ticket)

            if definitions:
                print(f"Definitions for '{term}':")

                # Language detection using regex patterns
                english_pattern = re.compile(r'^[a-zA-Z0-9\s.,\-\'()]+$')

                # Filter definitions based on preferred language
                filtered_definitions = []

                for definition in definitions:
                    if preferred_language == 'english' and english_pattern.match(definition):
                        filtered_definitions.append(definition)

                # Print filtered definitions
                if filtered_definitions:
                    for idx, definition in enumerate(filtered_definitions, 1):
                        print(f"{idx}. {definition}")
                else:
                    print(f"No definitions available for term '{term}' in {preferred_language}.")
            else:
                print(f"No definitions available for term '{term}'.")
        else:
            print(f"Could not find CUI for term '{term}'.")

    except Exception as e:
        print(f"Error: {str(e)}")

# Example usage
get_medical_term_definitions('osteoarthritis', preferred_language='english')
