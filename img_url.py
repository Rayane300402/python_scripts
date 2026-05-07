import tkinter as tk
from tkinter import filedialog
import os
import requests
from dotenv import load_dotenv
import pyperclip

def main():
    print('Starting Main')
    
    root = tk.Tk()
    root.withdraw()
    
    api_key = configureImageBB()
    
    if not api_key:
        return
    
    imgToURL(api_key)
    
    print('Goodbye!!')
        

def imgToURL(api_key):
    print('Do you want to turn an image into a url')
    file_path = fetchFilePath()
    
    if file_path:
        print(f"Selected file: {file_path}" )
        
   
        res = imagebbFetch(file_path, api_key)
        
        if res:
            while True:
                data = input('Do you wish to continue? Y/n: ').lower()

                if data == 'y' :
                    print('Continuing...')
                    imgToURL(api_key)
                    break
                elif data == 'n' :
                    print('Exiting...')
                    break
                else: 
                    print('Please Enter Y/y or N/n')
            return
             
        else:
            print("An error occured")
            return 
            
    else: 
        print("No file selected")
        return 
     
        
       
def fetchFilePath():
    file_types = [('Image Files', '*.png;*.jpg;*.jpeg')]
    
    file_path = filedialog.askopenfilename(
        title='Select an Image',
        filetypes=file_types
    )
    
    return file_path
    
def imagebbFetch(file_path, api_key):
    print("Uploading Image...")
    
    url = "https://api.imgbb.com/1/upload"
    
    with open(file_path, "rb") as image_file:
       response = requests.post(
           url,
           params={"key": api_key},
           files={"image": image_file}
       )

    result = response.json()

    if result.get("success"):
        image_url = result["data"]["url"]
        print("Image URL:")
        print(image_url)
        print('Copying it....')
        pyperclip.copy(image_url)
        print("Copied!")
        return image_url

    print("Upload failed")
    print(result)
    return None

def configureImageBB():
    load_dotenv()
    
    api_key = os.getenv("IMGBB_API_KEY")
    
    if not api_key:
        print("Missing IMGBB_API_KEY in .env")
        return None
    
    print("ImgBB configured")
    return api_key


if __name__ == "__main__":
    main()
