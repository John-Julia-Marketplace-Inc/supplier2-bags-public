from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor, as_completed
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import time
import pandas as pd
import os
from clean_data import final_prep
from selenium.common.exceptions import NoSuchElementException, TimeoutException

file_path = 'private_repo/clean_data/products_slower.csv'

SUPPLIER_URL = os.getenv('SUPPLIER_URL')

LOGIN = os.getenv('LOGIN')
PASSWORD = os.getenv('PASSWORD')

fabric_list = [
    'brass', 'sheep shearling', 'buffalo leather', 'synthetic raffia', 'sheep shearling; calfskin details',
    'cow leather', 'cowhide leather', 'faux leather', 'lambskin', 'bull leather', 'goatskin', 'lamb shearling',
    'calfskin details', 'calf hair', 'calfskin', 'deerskin', 'bovine leather', 'ovine leather'
]

country_list = ['spain', 'italy', 'france', 'eu', 'portugal']

if os.path.exists(file_path):
    os.remove(file_path)

def get_general_info(driver):
    product_name = brand_name = product_image_links_str = color = fabric = country = description = None
    width = height = depth = "N/A"
    
    try:
        description = driver.find_element(By.ID, 'tab-description').text
    except Exception as e:
        print(f"Error getting product description: {e}")
    
    try:
        product_images = driver.find_elements(By.CSS_SELECTOR, 'div.single-image img')
        product_image_links = [img.get_attribute('data-image-full') for img in product_images][:4]
        product_image_links_str = ', '.join(product_image_links)
    except Exception as e:
        print(f"Error getting product images: {e}")

    try:
        brand_name = driver.find_element(By.CSS_SELECTOR, 'span.product-brand a').get_attribute('title')
    except Exception as e:
        print(f"Error getting brand name: {e}")

    try:
        product_name = driver.find_element(By.CSS_SELECTOR, 'span.product-name').text
    except Exception as e:
        print(f"Error getting product name: {e}")
    
    try: 
        discounted_cost = driver.find_element(By.CSS_SELECTOR, 'span.special-price.discountedprice span.price').text
    except:
        discounted_cost = "N/A"

    try:
        not_discounted_cost = driver.find_element(By.CSS_SELECTOR, 'span.old-price.oldpricelisting span.price').text
    except:
        not_discounted_cost = "N/A"
        
    try:
        if discounted_cost == "N/A" and not_discounted_cost == "N/A":
            price_element = driver.find_element(By.CSS_SELECTOR, 'div.product-info-price div.price-final_price span.price-wrapper span.price')
            if price_element:
                price = price_element.text.strip()
    except Exception as e:
        print(f"Error getting price: {e}")
    
    product_code = 'N/A'
    
    try:
        if product_code == "N/A":
            product_code_element = driver.find_element(By.CSS_SELECTOR, 'div.product-code.mt-5 span')
            product_code = product_code_element.text.split(":")[1].strip()
    except Exception as e:
        print(f"Error finding product code: {e}")

    details = driver.find_element(By.CSS_SELECTOR, 'div.tab-pane#tab-description').find_elements(By.TAG_NAME, 'li')
    if details:
        for detail in details:
            text = detail.text.lower()
            if 'color' in text or 'colour' in text:
                color = text.split(':')[-1].strip()
            elif 'made in' in text:
                country = text.split('made in')[-1].strip()
            elif 'cm' in text:
                dimensions = text.split('cm')[0].strip().split('x')
                if len(dimensions) == 3:
                    dimensions = [d.strip() for d in dimensions]
                    width = dimensions[0] + ' cm'
                    height = dimensions[1] + ' cm'
                    depth = dimensions[2] + ' cm'
    
    if discounted_cost != 'N/A':    
        return product_name, brand_name, product_image_links_str, discounted_cost, not_discounted_cost, product_code, color, country, width, height, depth, description
    else:
        return product_name, brand_name, product_image_links_str, price, price, product_code, color, country, width, height, depth, description

def get_details(driver):
    color = fabric = country = "N/A"
    
    try:
        details_tab = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-bs-target="#tab-details"]'))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", details_tab)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", details_tab)
        
        WebDriverWait(driver, 2).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.tab-pane#tab-details'))
        )
        
        details = driver.find_element(By.CSS_SELECTOR, 'div.tab-pane#tab-details').find_elements(By.TAG_NAME, 'li')
        
        for detail in details:
            text = detail.text.lower()
            if 'color' in text or 'colour' in text:
                color = detail.text.split(':')[-1].strip()
            elif 'made in' in text:
                country = detail.text.split('made in')[-1].strip()
            elif any(f.lower() in text for f in fabric_list):
                fabric = detail.text.strip()
            elif any(c.lower().strip() in text for c in country_list):
                country = detail.text.strip()
    
    except Exception as e:
        print(f"Error getting details: {e}")
    
    return color, fabric, country


def get_size_details(driver, dimensions):
    dim = dimensions.copy()
    
    try:
        size_fit_tab = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-bs-target="#tab-sizeandfit"]'))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", size_fit_tab)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", size_fit_tab)
        
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.tab-pane#tab-sizeandfit'))
        )
        
        size_and_fit = driver.find_element(By.CSS_SELECTOR, 'div.tab-pane#tab-sizeandfit').find_elements(By.TAG_NAME, 'li')
        for size in size_and_fit:
            if "Width" in size.text:
                dim["Width"] = size.text.split(" ")[1] + ' cm'
            elif "Height" in size.text:
                dim["Height"] = size.text.split(" ")[1] + ' cm'
            elif "Depth" in size.text:
                dim["Depth"] = size.text.split(" ")[1] + ' cm'
            elif "Handle drop" in size.text:
                dim["Handle Drop"] = size.text.split(" ")[2] + ' cm'
    except Exception as e:
        print(f"Error getting size details: {e}")
    
    return dim

def get_products(driver, product_items, collection):
    for item in product_items:
        try:
            product_link = item.find_element(By.CSS_SELECTOR, 'a.product-item-link').get_attribute('href')
            driver.execute_script("window.open(arguments[0]);", product_link)
            driver.switch_to.window(driver.window_handles[-1])

            WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.single-image img'))
            )

            dimensions = {
                "Width": "N/A",
                "Height": "N/A",
                "Depth": "N/A",
                "Handle Drop": "N/A"
            }

            product_name, brand_name, product_image_links_str, discounted_cost, not_discounted_cost, product_code, color, country, width, height, depth, description = get_general_info(driver)
            
            if not color or not country or width == "N/A" or height == "N/A" or depth == "N/A":
                color, fabric, country = get_details(driver)
                dimensions = get_size_details(driver, dimensions)
                width = dimensions['Width']
                height = dimensions['Height']
                depth = dimensions['Depth']

            stock_status = 'In Stock'
            try:
                stock_status = driver.find_element(By.CSS_SELECTOR, 'div.outofstockpdp').text
            except:
                pass


            image_dict = {f"Image{i+1}": link for i, link in enumerate(product_image_links_str.split(', '))}

            if stock_status == 'In Stock':
                inventory = 2
            else:
                inventory = 0

            department = 'female' if 'women' in collection.lower() else 'male'
            gender = 'womenswear' if department == 'female' else 'menswear'

            if 'made in' in country.lower():
                country = country.split('in')[-1].strip()

            pd.DataFrame({
                'Product Name': [product_name], 'Brand Name': [brand_name],
                'Description': [description],
                'Color': [color.replace('color', '').strip(', ').title()], 'Country': [country.replace('made in', '').strip().title()],
                'Fabric': [fabric.title()],
                'Width': [width.strip()],  'Height': [height.strip()], 
                'Depth': [depth.strip()], 'Handle Drop': [dimensions['Handle Drop'].strip()],
                'Price': [discounted_cost.replace('"', '').replace(',', '')],
                'Compare At Price': [not_discounted_cost.replace('"', '').replace(',', '')],
                'Inventory': [inventory], 'Product Code': [product_code],
                'gender': [gender], 'Department': [department], 
                'Stock Status': [stock_status], 'Collection': [collection],
                'Images': [','.join([v for v in image_dict.values()])]
            }).to_csv(file_path, mode='a', header=not os.path.exists(file_path), index=False)

            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        except Exception as e:
            print(f"Error processing product: {e}")
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            continue


def get_info(url, collection, page_range):
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(3)

        # # Login on the first page
        # username_field = driver.find_element(By.NAME, 'login[username]')
        # password_field = driver.find_element(By.NAME, 'login[password]')
        # username_field.send_keys(LOGIN)
        # password_field.send_keys(PASSWORD)
        # password_field.send_keys(Keys.RETURN)
        # time.sleep(2)

        # print('Logged in successfully!')
        
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless=new")
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            time.sleep(3)

            # Retry mechanism for login with visibility check for the product list
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Locate the login fields
                    username_field = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.NAME, 'login[username]'))
                    )
                    password_field = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.NAME, 'login[password]'))
                    )

                    # Input credentials
                    username_field.clear()
                    password_field.clear()
                    username_field.send_keys(LOGIN)
                    password_field.send_keys(PASSWORD)
                    password_field.send_keys(Keys.RETURN)
                    time.sleep(2)

                    # Check for visibility of the product list element
                    product_list_visible = WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, 'ol.products.list.items.product-items.row'))
                    )
                    
                    if product_list_visible:
                        print('Product list is visible, login successful!')
                        break

                    # If the element is not visible, raise an exception to retry
                    raise Exception("Product list not visible, retrying login...")
                except (NoSuchElementException, TimeoutException, Exception) as login_error:
                    print(f"Login attempt {attempt + 1} failed: {login_error}")
                    if attempt == max_retries - 1:
                        print(f"All {max_retries} login attempts failed.")
                        driver.quit()
                        raise Exception("Failed to log in and find product list after 3 attempts.")
                    time.sleep(2)  # Short wait before retrying
        except Exception as e:
            print(f"Error in get_info: {e}")
        
        
        # Handle different page_range inputs: 'all', '18', '1,6'
        if page_range == 'all':
            page_number = 1
            
            while True:
                driver.get(f"{url}?p={page_number}")
                # Extract products and process the page
                product_list = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'ol.products.list.items.product-items.row'))
                )
                product_items = product_list.find_elements(By.CSS_SELECTOR, 'li.item.product.product-item.pb-5.col-6.col-md-6.col-lg-3')

                # Process each product item (you can use your existing logic for this)
                for item in product_items:
                    try:
                        product_link = item.find_element(By.CSS_SELECTOR, 'a.product-item-link').get_attribute('href')
                        driver.execute_script("window.open(arguments[0]);", product_link)
                        driver.switch_to.window(driver.window_handles[-1])

                        WebDriverWait(driver, 2).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.single-image img'))
                        )

                        dimensions = {
                            "Width": "N/A",
                            "Height": "N/A",
                            "Depth": "N/A",
                            "Handle Drop": "N/A"
                        }

                        product_name, brand_name, product_image_links_str, discounted_cost, not_discounted_cost, product_code, color, country, width, height, depth, description = get_general_info(driver)
                        
                        if not color or not country or width == "N/A" or height == "N/A" or depth == "N/A":
                            color, fabric, country = get_details(driver)
                            dimensions = get_size_details(driver, dimensions)
                            width = dimensions['Width']
                            height = dimensions['Height']
                            depth = dimensions['Depth']

                        stock_status = 'In Stock'
                        try:
                            stock_status = driver.find_element(By.CSS_SELECTOR, 'div.outofstockpdp').text
                        except:
                            pass


                        image_dict = {f"Image{i+1}": link for i, link in enumerate(product_image_links_str.split(', '))}

                        if stock_status == 'In Stock':
                            inventory = 2
                        else:
                            inventory = 0

                        breadcrumb_elements = driver.find_elements(By.CSS_SELECTOR, 'div.breadcrumbs ul.items li')
                        breadcrumbs = ' > '.join([breadcrumb.text.strip() for breadcrumb in breadcrumb_elements])

                        department = 'female' if 'women' in collection.lower() else 'male'
                        gender = 'womenswear' if department == 'female' else 'menswear'

                        if 'made in' in country.lower():
                            country = country.split('in')[-1].strip()

                        pd.DataFrame({
                            'Product Name': [product_name], 'Brand Name': [brand_name],
                            'Description': [description],
                            'Color': [color.replace('color', '').strip(', ').title()], 'Country': [country.replace('made in', '').strip().title()],
                            'Fabric': [fabric.title()],
                            'Breadcrumbs': [breadcrumbs],
                            'Width': [width.strip()],  'Height': [height.strip()], 
                            'Depth': [depth.strip()], 'Handle Drop': [dimensions['Handle Drop'].strip()],
                            'Price': [discounted_cost.replace('"', '').replace(',', '')],
                            'Compare At Price': [not_discounted_cost.replace('"', '').replace(',', '')],
                            'Inventory': [inventory], 'Product Code': [product_code],
                            'gender': [gender], 'Department': [department], 
                            'Stock Status': [stock_status], 'Collection': [collection],
                            'Images': [','.join([v for v in image_dict.values()])]
                        }).to_csv(file_path, mode='a', header=not os.path.exists(file_path), index=False)

                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])

                    except Exception as e:
                        print(f"Error processing product: {e}")
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        continue

                # Check for next page button
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, 'li.pages-item-next > a.action.next')
                    next_button.click()
                    page_number += 1
                    time.sleep(5)
                except Exception as e:
                    print(f"No more pages...")
                    break  # Exit the loop when no next button is found

        elif ',' in page_range:  # Handle ranges like '1,6'
            start_page, end_page = map(int, page_range.split(','))
            for page_number in range(start_page, end_page + 1):
                driver.get(f"{url}?p={page_number}")
                time.sleep(5)

                # Extract products and process the page (similar to above)
                product_list = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'ol.products.list.items.product-items.row'))
                )
                product_items = product_list.find_elements(By.CSS_SELECTOR, 'li.item.product.product-item.pb-5.col-6.col-md-6.col-lg-3')

                # Process each product item (you can use your existing logic for this)
                for item in product_items:
                    try:
                        product_link = item.find_element(By.CSS_SELECTOR, 'a.product-item-link').get_attribute('href')
                        driver.execute_script("window.open(arguments[0]);", product_link)
                        driver.switch_to.window(driver.window_handles[-1])

                        WebDriverWait(driver, 2).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.single-image img'))
                        )

                        dimensions = {
                            "Width": "N/A",
                            "Height": "N/A",
                            "Depth": "N/A",
                            "Handle Drop": "N/A"
                        }

                        product_name, brand_name, product_image_links_str, discounted_cost, not_discounted_cost, product_code, color, country, width, height, depth, description = get_general_info(driver)
                        
                        if not color or not country or width == "N/A" or height == "N/A" or depth == "N/A":
                            color, fabric, country = get_details(driver)
                            dimensions = get_size_details(driver, dimensions)
                            width = dimensions['Width']
                            height = dimensions['Height']
                            depth = dimensions['Depth']

                        stock_status = 'In Stock'
                        try:
                            stock_status = driver.find_element(By.CSS_SELECTOR, 'div.outofstockpdp').text
                        except:
                            pass

                        breadcrumb_elements = driver.find_elements(By.CSS_SELECTOR, 'div.breadcrumbs ul.items li')
                        breadcrumbs = ' > '.join([breadcrumb.text.strip() for breadcrumb in breadcrumb_elements])
                        
                        image_dict = {f"Image{i+1}": link for i, link in enumerate(product_image_links_str.split(', '))}

                        if stock_status == 'In Stock':
                            inventory = 2
                        else:
                            inventory = 0

                        department = 'female' if 'women' in collection.lower() else 'male'
                        gender = 'womenswear' if department == 'female' else 'menswear'

                        if 'made in' in country.lower():
                            country = country.split('in')[-1].strip()

                        pd.DataFrame({
                            'Product Name': [product_name], 'Brand Name': [brand_name],
                            'Description': [description],
                            'Color': [color.replace('color', '').strip(', ').title()], 'Country': [country.replace('made in', '').strip().title()],
                            'Fabric': [fabric.title()],
                            'Breadcrumbs': [breadcrumbs],
                            'Width': [width.strip()],  'Height': [height.strip()], 
                            'Depth': [depth.strip()], 'Handle Drop': [dimensions['Handle Drop'].strip()],
                            'Price': [discounted_cost.replace('"', '').replace(',', '')],
                            'Compare At Price': [not_discounted_cost.replace('"', '').replace(',', '')],
                            'Inventory': [inventory], 'Product Code': [product_code],
                            'gender': [gender], 'Department': [department], 
                            'Stock Status': [stock_status], 'Collection': [collection],
                            'Images': [','.join([v for v in image_dict.values()])]
                        }).to_csv(file_path, mode='a', header=not os.path.exists(file_path), index=False)

                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])

                    except Exception as e:
                        print(f"Error processing product: {e}")
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        continue

        else:  # Handle single number like '18'
            start_page = int(page_range)
            page_number = start_page
            while True:
                driver.get(f"{url}?p={page_number}")
                time.sleep(5)

                # Extract products and process the page (similar to above)
                product_list = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'ol.products.list.items.product-items.row'))
                )
                product_items = product_list.find_elements(By.CSS_SELECTOR, 'li.item.product.product-item.pb-5.col-6.col-md-6.col-lg-3')

                # Process each product item (you can use your existing logic for this)
                for item in product_items:
                    try:
                        product_link = item.find_element(By.CSS_SELECTOR, 'a.product-item-link').get_attribute('href')
                        driver.execute_script("window.open(arguments[0]);", product_link)
                        driver.switch_to.window(driver.window_handles[-1])

                        WebDriverWait(driver, 2).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.single-image img'))
                        )

                        dimensions = {
                            "Width": "N/A",
                            "Height": "N/A",
                            "Depth": "N/A",
                            "Handle Drop": "N/A"
                        }

                        product_name, brand_name, product_image_links_str, discounted_cost, not_discounted_cost, product_code, color, country, width, height, depth, description = get_general_info(driver)
                        
                        if not color or not country or width == "N/A" or height == "N/A" or depth == "N/A":
                            color, fabric, country = get_details(driver)
                            dimensions = get_size_details(driver, dimensions)
                            width = dimensions['Width']
                            height = dimensions['Height']
                            depth = dimensions['Depth']

                        stock_status = 'In Stock'
                        try:
                            stock_status = driver.find_element(By.CSS_SELECTOR, 'div.outofstockpdp').text
                        except:
                            pass

                        breadcrumb_elements = driver.find_elements(By.CSS_SELECTOR, 'div.breadcrumbs ul.items li')
                        breadcrumbs = ' > '.join([breadcrumb.text.strip() for breadcrumb in breadcrumb_elements])

                        image_dict = {f"Image{i+1}": link for i, link in enumerate(product_image_links_str.split(', '))}

                        if stock_status == 'In Stock':
                            inventory = 2
                        else:
                            inventory = 0

                        department = 'female' if 'women' in collection.lower() else 'male'
                        gender = 'womenswear' if department == 'female' else 'menswear'

                        if 'made in' in country.lower():
                            country = country.split('in')[-1].strip()

                        pd.DataFrame({
                            'Product Name': [product_name], 'Brand Name': [brand_name],
                            'Description': [description],
                            'Color': [color.replace('color', '').strip(', ').title()], 'Country': [country.replace('made in', '').strip().title()],
                            'Fabric': [fabric.title()],
                            'Breadcrumbs': [breadcrumbs],
                            'Width': [width.strip()],  'Height': [height.strip()], 
                            'Depth': [depth.strip()], 'Handle Drop': [dimensions['Handle Drop'].strip()],
                            'Price': [discounted_cost.replace('"', '').replace(',', '')],
                            'Compare At Price': [not_discounted_cost.replace('"', '').replace(',', '')],
                            'Inventory': [inventory], 'Product Code': [product_code],
                            'gender': [gender], 'Department': [department], 
                            'Stock Status': [stock_status], 'Collection': [collection],
                            'Images': [','.join([v for v in image_dict.values()])]
                        }).to_csv(file_path, mode='a', header=not os.path.exists(file_path), index=False)

                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])

                    except Exception as e:
                        print(f"Error processing product: {e}")
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        continue

                # Check for next page button
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, 'li.pages-item-next > a.action.next')
                    next_button.click()
                    page_number += 1
                    time.sleep(5)
                except Exception as e:
                    print(f"No more pages...")
                    break  # Exit the loop when no next button is found

        driver.quit()

    except Exception as e:
        print(f"Error in get_info: {e}")

        

if __name__ == "__main__":    
    start_time = time.time()
    collections = ["Women's Wallets", 
                   "Men's Wallets", "Men's Wallets", 
                   "Men's Bags", "Men's Bags", 
                   "Women's Bags", "Women's Bags", "Women's Bags", "Women's Bags", "Women's Bags", "Women's Bags", "Women's Bags"]

    urls = [
        f'{SUPPLIER_URL}/vip2_en/women/accessories/wallets.html',
        
        f'{SUPPLIER_URL}/vip2_en/men/accessories/wallets.html',
        f'{SUPPLIER_URL}/vip2_en/men/accessories/wallets.html',
        
        f'{SUPPLIER_URL}/vip2_en/men/bags.html',
        f'{SUPPLIER_URL}/vip2_en/men/bags.html',
        
        f'{SUPPLIER_URL}/vip2_en/women/bags.html',
        f'{SUPPLIER_URL}/vip2_en/women/bags.html',
        f'{SUPPLIER_URL}/vip2_en/women/bags.html',
        f'{SUPPLIER_URL}/vip2_en/women/bags.html',
        f'{SUPPLIER_URL}/vip2_en/women/bags.html',
        f'{SUPPLIER_URL}/vip2_en/women/bags.html',
        f'{SUPPLIER_URL}/vip2_en/women/bags.html',
    ]
    
    pages = [
        'all', 
        '1,2', '3', 
        '1,3', '4',
        '1,3', '4,6', '7,9','10,13', '14,16', '17,19', '20'
    ]

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(get_info, url, collection, page) for url, collection, page in zip(urls, collections, pages)]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Exception occurred: {e}")

    final_prep()

    end_time = time.time()  
    execution_time = end_time - start_time

    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
    print(f"End time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
    print(f"Total execution time: {execution_time:.2f} seconds")
    