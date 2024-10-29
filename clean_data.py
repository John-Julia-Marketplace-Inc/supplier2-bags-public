import pandas as pd
import numpy as np
import re

def round_to_5_or_0(x):
    return np.round(x / 5) * 5

def round_to_nearest_10(x):
    return np.ceil(x / 10) * 10 

def fix_bags(data):
    bags = data[['Width', 'Height']]
    empty_bags = bags[(bags['Width'] == '0') & (bags['Height'] == '0')]
    data.loc[empty_bags.index, ['Width', 'Height']] = ''
    data['Dimensions'] = data.apply(lambda row: fix_bag_dim(row['Width'], row['Height'], row['Depth']), axis=1)
    return data

def fix_bag_dim(length, height, depth=None):
    # Handle cases where length or height are missing or invalid
    if length == 0 or height == 0 or length == '0' or height == '0' or isinstance(length, int):       
        return ''
    
    try:
        # Function to clean and convert the dimensions to float
        remove = lambda z: float(str(z).lower().replace('c', '').replace('m', '').replace(',', '.').replace('!', '').strip())
    
        # Convert length and height
        length, height = remove(length), remove(height)
        
        # Only convert depth if it is provided
        if depth is not None and depth != '' and depth != '0':
            depth = remove(depth)
        else:
            depth = None  # Mark depth as missing if it's not provided
    except ValueError:
        return ''
    
    # Convert to cm
    if depth is not None:
        cm = f'H {height} cm x L {length} cm x D {depth} cm'
    else:
        cm = f'H {height} cm x L {length} cm'
    
    # Conversion function from cm to inches
    cm_to_inch = lambda z: round(z / 2.54, 1)

    # Convert to inches
    length, height = cm_to_inch(length), cm_to_inch(height)
    if depth is not None:
        depth = cm_to_inch(depth)
        inches = f'H {height}" x L {length}" x D {depth}"'
    else:
        inches = f'H {height}" x L {length}"'
    
    # Return the final formatted string with cm and inches
    return f'{cm} / {inches}'


fabric_list = [
    'brass', 'sheep shearling', 'buffalo leather', 'synthetic raffia', 
    'sheep shearling; calfskin details', 'cow leather', 'cowhide leather', 
    'faux leather', 'lambskin', 'bull leather', 'goatskin', 'lamb shearling', 
    'calfskin details', 'calf hair', 'calfskin', 'deerskin', 'bovine leather', 
    'ovine leather', 'nylon', 'denim'
]

country_list = ['spain', 'italy', 'france', 'eu', 'portugal']

def find_country(description):
    for country in country_list:
        if country.lower() in description.lower():
            return country.capitalize()
    return '-'

# Function to extract fabric from the Description column
def extract_fabric(description):
    for fabric in fabric_list:
        if fabric.lower() in description.lower():
            return fabric.title()
    return '-'

# Function to extract NxN and NxNxN dimensions from the Description column
def extract_dimensions(description):
    match_nxn = re.search(r'\b\d+\s*x\s*\d+\b', description)  # Pattern for NxN
    match_nxnxn = re.search(r'\b\d+\s*x\s*\d+\s*x\s*\d+\b', description)  # Pattern for NxNxN
    
    if match_nxnxn:
        return match_nxnxn.group(), 'NxNxN'
    elif match_nxn:
        return match_nxn.group(), 'NxN'
    else:
        return None, None
    
    
def fix_dimensions(row):
    if row['Dimensions_Type'] == 'NxN':
        return [*[f'{x} cm' for x in row['Dimensions'].split('x')], 0]
    elif row['Dimensions_Type'] == 'NxNxN':
        return [f'{x} cm' for x in row['Dimensions'].split('x')]
    else:
        return [0, 0, 0]
    
def extract_color(description):
    match = re.search(r'color\s+([\w\s/-]+)', description, re.IGNORECASE)
    return match.group(1).split(' ')[0].strip().title().replace('\n', '') if match else '-'


breadcrumbs =  {
    'Wallets': 'Apparel & Accessories > Handbags, Wallets & Cases > Wallets & Money Clips > Wallets', 
    'Shoulder Bags': 'Apparel & Accessories > Handbags, Wallets & Cases > Handbags > Shoulder Bags', 
    'Shopper Bags': 'Apparel & Accessories > Handbags, Wallets & Cases > Handbags > Shopper Bags', 
    'Cross Body Bags': 'Apparel & Accessories > Handbags, Wallets & Cases > Handbags > Cross Body Bags', 
    'Baquette Handbags': 'Apparel & Accessories > Handbags, Wallets & Cases > Handbags > Baguette Handbags', 
    'Barrel Bags': 'Apparel & Accessories > Handbags, Wallets & Cases > Handbags > Barrel Bags', 
    'Beach Bags': 'Apparel & Accessories > Handbags, Wallets & Cases > Handbags > Beach Bags', 
    'Bucket Bags': 'Apparel & Accessories > Handbags, Wallets & Cases > Handbags > Bucket Bags', 
    'Clutch Bags': 'Apparel & Accessories > Handbags, Wallets & Cases > Handbags > Clutch Bags', 
    'Convertible Bags': 'Apparel & Accessories > Handbags, Wallets & Cases > Handbags > Convertible Bags', 
    'Doctor Bags': 'Apparel & Accessories > Handbags, Wallets & Cases > Handbags > Doctor Bags', 
    'Envelope Clutches': 'Apparel & Accessories > Handbags, Wallets & Cases > Handbags > Envelope Clutches', 
    'Fold Over Clutches': 'Apparel & Accessories > Handbags, Wallets & Cases > Handbags > Fold Over Clutches', 
    'Half-Moon Bags': 'Apparel & Accessories > Handbags, Wallets & Cases > Handbags > Half-Moon Bags', 
    'Hobo Bags': 'Apparel & Accessories > Handbags, Wallets & Cases > Handbags > Hobo Bags', 
    'Muff Clutches & Bags': 'Apparel & Accessories > Handbags, Wallets & Cases > Handbags > Muff Clutches & Bags', 
    'Saddle Bags': 'Apparel & Accessories > Handbags, Wallets & Cases > Handbags > Saddle Bags', 
    'Satchel Bags': 'Apparel & Accessories > Handbags, Wallets & Cases > Handbags > Satchel Bags',
    'School Bags': 'Apparel & Accessories > Handbags, Wallets & Cases > Handbags > School Bags', 
    'Trapezoid Bags': 'Apparel & Accessories > Handbags, Wallets & Cases > Handbags > Trapezoid Bags', 
    'Handbags': 'Apparel & Accessories > Handbags, Wallets & Cases > Handbags'
}

def fix_category(x):
    x = x.lower()
    
    if 'tote bag' in x or 'mini bag' in x or 'belt bag' in x or 'backpack' in x:
        return 'Handbags'
    elif 'shooping bag' in x or 'shopping bag' in x:
        return 'Shopper Bags'
    elif 'shoulder bag' in x:
        return 'Shoulder Bags'
    elif 'wallet' in x:
        return 'Wallets'
    elif 'cross body' in x or 'crossbody':
        return 'Cross Body Bags'
    elif 'baquette' in x:
        return 'Baquette Handbags'
    elif 'barrel' in x:
        return 'Barrel Bags'
    elif 'beach' in x:
        return 'Beach Bags'
    elif 'bucket' in x:
        return 'Bucket Bags'
    elif 'clutch' in x and not 'muff' in x:
        return 'Clutch Bags'
    elif 'convertible' in x:
        return 'Convertible Bags'
    elif 'doctor' in x:
        return 'Doctor Bags'
    elif 'envelope' in x:
        return 'Envelope Clutches'
    elif 'fold over' in x:
        return 'Fold Over Clutches'
    elif 'half' in x and 'moon' in x:
        return 'Half-Moon Bags'
    elif 'hobo' in x:
        return 'Hobo Bags'
    elif 'muff' in x:
        return 'Muff Clutches & Bags'
    elif 'saddle' in x:
        return 'Saddle Bags'
    elif 'school' in x:
        return 'School Bags'
    elif 'trapezoid' in x:
        return 'Trapezoid Bags'
    else:
        return 'Handbags'


def get_products(link):
    data = pd.read_csv(link)
    
    # Filter for rows with missing dimensions
    missing_dims = data[(data['Height'].isna()) | (data['Width'].isna())].copy()  # Use .copy() to avoid SettingWithCopyWarning

    # Process missing dimensions with .loc[]
    missing_dims.loc[:, 'Description'] = missing_dims['Description'].apply(lambda x: x.replace('made', ' made').replace('\n', ' '))
    missing_dims.loc[:, 'Color'] = missing_dims['Description'].apply(lambda x: extract_color(x))
    missing_dims.loc[:, 'Fabric'] = missing_dims['Description'].apply(lambda x: extract_fabric(x) if pd.notnull(x) else None)
    
    missing_dims[['Dimensions', 'Dimensions_Type']] = missing_dims['Description'].apply(
            lambda x: pd.Series(extract_dimensions(x)) if pd.notnull(x) else pd.Series([None, None])
        )

    for idx, row in missing_dims.iterrows():
        # Use .loc[] to update the original data
        data.loc[idx, ['Width', 'Height', 'Depth']] = fix_dimensions(row)
    
    # Update fabric and color in original data
    data.loc[missing_dims.index, 'Fabric'] = missing_dims['Fabric']
    data.loc[missing_dims.index, 'Color'] = missing_dims['Color'].apply(lambda x: x.split('\n')[0] if isinstance(x, str) and '\n' in x else x)
    
    data['Product Name'] = data['Product Name'].apply(lambda x: x.title().replace('\n', '-'))
    data['Description'] = data['Description'].apply(lambda x: x.replace('made', ' made ').replace('\n', ' ').strip())
    data['Category'] = data["Product Name"].apply(lambda x: fix_category(x))
    
    # Ensure numeric conversions and formatting are handled safely
    data['Width'] = data['Width'].apply(lambda x: x.replace('"', '').replace(',', '.') if isinstance(x, str) else '')
    data['Height'] = data['Height'].apply(lambda x: x.replace('"', '').replace(',', '.') if isinstance(x, str) else '')
    data['Depth'] = data['Depth'].apply(lambda x: x.replace('"', '').replace(',', '.') if isinstance(x, str) else '')
    
    # Convert prices
    data['Price'] = data['Price'].apply(lambda x: float(str(x).replace('€', '').replace(',', '').strip()))
    data['Compare At Price'] = data['Compare At Price'].apply(lambda x: float(str(x).replace('€', '').replace(',', '').strip()))
    
    # Perform conversions and rounding
    data['Price'] *= 1.08
    data['Compare At Price'] *= 1.08
    
    data['Unit Cost'] = data['Price']
    data['Price'] *= 1.25
    data['Price'] = data['Price'].apply(lambda x: round_to_5_or_0(x))
    data['Compare At Price'] = data['Price'].apply(lambda x: round_to_5_or_0(x * 1.45))
    
    data['gender'] = data['gender'].apply(lambda x: x.title())
    
    data = fix_bags(data)
    
    # data['Breadcrumbs'] = data['Category'].apply(lambda x: breadcrumbs.get(x, breadcrumbs['Handbags']))
    data['Breadcrumbs'] = data['Breadcrumbs'].apply(lambda x: '>'.join(x.split('>')[1:-1]))
    data['Taxonomy'] = data['Collection'].apply(lambda x: 330 if 'Wallet' in x else 329)

    def get_images(x):
        split = x.split(',')
        return [split[i] if i < len(split) else None for i in range(4)]

    data[['Image1', 'Image2', 'Image3', 'Image4']] = data['Images'].apply(lambda x: pd.Series(get_images(x)))

    # Fix missing countries
    missing_countries = data[data['Country'].isna()].copy()  # Use .copy() to avoid SettingWithCopyWarning
    missing_countries.loc[:, 'Country'] = missing_countries['Description'].apply(lambda x: find_country(x))
    
    # Update the original DataFrame
    data.loc[missing_countries.index, 'Country'] = missing_countries['Country']
    data['Fabric'] = data['Fabric'].apply(lambda x: x.replace('Fabric', '').replace('.', '').replace(',', '').strip() if isinstance(x, str) else '')
    
    # Remove rows with invalid dimensions
    data.to_csv('private_repo/clean_data/cleaned_data.csv', index=False)
    return data
    

def final_prep():
    data = get_products('private_repo/clean_data/products_slower.csv')
    
    out_of_stock = data[data['Stock Status'] == 'OUT OF STOCK']
    print('Number of out of stock products:', out_of_stock)
    out_of_stock.to_csv('private_repo/clean_data/out_of_stock.csv')
    
    data.drop(index=out_of_stock.index, inplace=True)
    data = data[data['Price'] != 'Price']
    
    # update all the products
    data.to_csv('private_repo/clean_data/to_update.csv', index=False)
    
    # read all existing SKUs
    non_existing_skus = pd.read_csv('private_repo/clean_data/existing_skus.csv')
    
    # clean up to not pass in broken products
    data = data[data['Inventory'] > 0]
    data = data[data['Compare At Price'] > 0]
    # data = data[data['Country'] != '-']
    data = data[data['Product Code'].str.len() > 0]
    
    non_existing_skus[~non_existing_skus['Variant SKU'].isin(data['Product Code'])].to_csv('private_repo/clean_data/zero_inventory.csv', index=False)
    
    # drop invalid entries
    print('Before removing invalid dimensions:', len(data))
    
    data = data[~data['Width'].str.contains('SIZE')]
    data = data[~data['Height'].str.contains('SIZE')]
    data = data[~data['Width'].str.contains('Width')]
    
    print('After removing invalid dimensions:', len(data))
    
    # pass in the files that are not in the skus
    to_create = data[~data['Product Code'].isin(non_existing_skus['Variant SKU'].values.tolist())]
    to_create.to_csv('private_repo/clean_data/to_create.csv', index=False)
    
    all_skus = pd.read_csv('private_repo/clean_data/existing_skus.csv')
    all_skus.rename(columns={'Variant SKU': 'Product Code'}, inplace=True)
    all_skus = pd.concat([all_skus['Product Code'], to_create['Product Code']], ignore_index=True)
    all_skus = pd.DataFrame({'Variant SKU': [x for x in all_skus.values.tolist() if len(x) > 0]})
    all_skus.dropna().to_csv('private_repo/clean_data/existing_skus.csv', index=False)
    
    
    data = pd.read_csv('private_repo/clean_data/products_slower.csv')
    data[data['Stock Status'] == 'OUT OF STOCK']['Product Code'].to_csv('private_repo/clean_data/out_of_stock.csv', index=False)
    