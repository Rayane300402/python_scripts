import tkinter as tk
from tkinter import filedialog
import os
import requests
from dotenv import load_dotenv
import pyperclip

def browseImage(path_entry):
    file_path = fetchFilePath()

    if file_path:
        path_entry.delete(0, tk.END)
        path_entry.insert(0, file_path)
        
def imgToURL(api_key, path_entry, url_entry, status_label, root):
    file_path = path_entry.get()

    if not file_path:
        showToast(status_label, root, "Please choose an image first")
        return

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

        url_entry.delete(0, tk.END)
        url_entry.insert(0, image_url)

        showToast(status_label, root, "Uploaded successfully!")
        return image_url

    showToast(status_label, root, "Upload failed")
    print(result)


def copyURL(url_entry, status_label, root):
    url = url_entry.get()

    if not url:
        showToast(status_label, root, "No URL to copy")
        return

    pyperclip.copy(url)
    showToast(status_label, root, "Copied!")


def showToast(status_label, root, message):
    status_label.config(text=message)

    root.after(2000, lambda: status_label.config(text=""))

def main():
    root = tk.Tk()
    
    api_key = configureImageBB()
    
    if not api_key:
        return

    root.title("Image to URL")
    root.geometry("500x300")
    
    title_label = tk.Label(
        root,
        text="Image to URL Converter",
        font=("Arial", 18)
    )

    title_label.pack(pady=20)

    path_entry = tk.Entry(
        root,
        width=50
    )
    
    path_entry.pack(pady=10)
    
    browse_button = tk.Button(
        root,
        text="Browse Image",
        command=lambda:browseImage(path_entry)
    )
    
    browse_button.pack()
    
    url_entry = tk.Entry(
    root,
    width=50
    )

    url_entry.pack(pady=20)

    button_frame = tk.Frame(root)
    button_frame.pack(pady=5)

    convert_button = tk.Button(
        button_frame,
        text="Convert Image",
        command=lambda: imgToURL(api_key, path_entry, url_entry, status_label, root)
    )

    convert_button.pack(side=tk.LEFT, padx=5)

    copy_button = tk.Button(
        button_frame,
        text="Copy URL",
        command=lambda: copyURL(url_entry, status_label, root)
    )

    copy_button.pack(side=tk.LEFT, padx=5)

    status_label = tk.Label(
        root,
        text="",
        font=("Arial", 10)
    )

    status_label.pack(pady=10)
    
    root.mainloop()
    
def configureImageBB():
    load_dotenv()
    
    api_key = os.getenv("IMGBB_API_KEY")
    
    if not api_key:
        print("Missing IMGBB_API_KEY in .env")
        return None
    
    print("ImgBB configured")
    return api_key


def fetchFilePath():
    file_types = [('Image Files', '*.png;*.jpg;*.jpeg')]
    
    file_path = filedialog.askopenfilename(
        title='Select an Image',
        filetypes=file_types
    )
    
    return file_path
    
if __name__ == "__main__":
    main()