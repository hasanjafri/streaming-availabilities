import geoip2.webservice
from justwatch import JustWatch
from os import environ
import requests
from threading import Timer
import tkinter as tk

from providers import PROVIDERS

def get_ip_address():
    response = requests.get('https://httpbin.org/ip')
    data = response.json()
    return data['origin']

def detect_country():
    # Get the user's IP address
    ip_address = get_ip_address()  # You can use a different IP address here

    # Look up the country for the IP address
    with geoip2.webservice.Client(environ['ACCOUNT_ID'], environ['LICENSE_KEY'], host='geolite.info') as client:
        response = client.city(ip_address)
        return response.country.iso_code

just_watch = JustWatch(country=detect_country())

# Make a request to the API and return the results
def search_api(query):
    results = just_watch.search_for_item(query=query, content_types=['movie', 'show'])
    print(results)
    return results['items']

# Make a request to the details API and return the results
def details_api(id, type):
    results = []
    if type == 'movie':
        results = just_watch.get_title(id)
    elif type == 'show':
        results = just_watch.get_title(id, content_type='show')
    print(results)
    return results

# Debounce helper function
def debounce(wait):
    """ Decorator that will postpone a functions
        execution until after `wait` seconds
        have elapsed since the last time it was invoked. """
    def decorator(fn):
        def debounced(*args, **kwargs):
            def call_it():
                fn(*args, **kwargs)
            try:
                debounced.t.cancel()
            except(AttributeError):
                pass
            debounced.t = Timer(wait, call_it)
            debounced.t.start()
        return debounced
    return decorator

# Create the main window
window = tk.Tk()
window.title("Streaming Availabilities of Movies and TV Shows")
window.geometry("666x666")

# Create the search bar
search_var = tk.StringVar()
search_bar = tk.Entry(window, textvariable=search_var)
search_bar.pack(side="top", fill="x")

# Create a frame to hold the scrollable view of the results
result_frame = tk.Frame(window)
result_frame.pack(side="top", fill="both", expand=True)

# Create a scrollable view of the results
scrollbar = tk.Scrollbar(result_frame)
canvas = tk.Canvas(result_frame, yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")
scrollbar.config(command=canvas.yview)
canvas.pack(side="left", fill="both", expand=True)

# Create a frame to hold the results
results_inner_frame = tk.Frame(canvas)
canvas.create_window((0, 0), window=results_inner_frame, anchor="nw")

# Function to update the scrollable view
def update_scrollable_view():
    # Update the scrollregion of the canvas
    canvas.config(scrollregion=canvas.bbox("all"))
    # Update the size of the inner frame to fit the contents
    results_inner_frame.update_idletasks()
    canvas.config(width=results_inner_frame.winfo_reqwidth())
    canvas.config(height=results_inner_frame.winfo_reqheight())

def get_provider_clear_name(short_name):
    for provider in PROVIDERS:
        if provider['short_name'] == short_name:
            return provider['clear_name']
    return None

def on_click(id, type='movie'):
    # Make a request to the details API
    details = details_api(id, type)
    # Create a new window to display the details
    details_window = tk.Toplevel(window)
    details_window.geometry("666x666")
    # Create a frame to hold the details
    details_frame = tk.Frame(details_window)
    details_frame.pack(side="top", fill="both", expand=True)
    # Update the display with the details
    title_label = tk.Label(details_frame, text=details["title"], font=("Helvetica", 16))
    title_label.pack(side="top", fill="x", pady=(4, 4))
    release_year_label = tk.Label(details_frame, text=f"Released in {details['original_release_year']}", font=("Helvetica", 14))
    release_year_label.pack(side="top", fill="x", pady=(0, 4))
    short_description_label = tk.Label(details_frame, text=details["short_description"], font=("Helvetica", 14), wraplength=600)
    short_description_label.pack(side="top", fill="x", pady=(0, 4))
    offers_label = tk.Label(details_frame, text="Available to Stream:", font=("Helvetica", 14))
    offers_label.pack(side="top", fill="x", pady=(4, 4))
    for offer in details["offers"]:
        # Use the get method to get the retail price, with a default value of "N/A"
        retail_price = offer.get("retail_price", "N/A")
        offer_short_name = offer['package_short_name']
        provider_clear_name = get_provider_clear_name(offer_short_name)
        offer_text = f"{provider_clear_name} - {offer['presentation_type']} - {offer['monetization_type']} {offer['currency']} {retail_price}"
        offer_label = tk.Label(details_frame, text=offer_text, font=("Helvetica", 14))
        offer_label.pack(side="top", fill="x", pady=(0, 4))

# Create a function to search the API and update the results
@debounce(0.5)
def search():
    query = search_var.get()
    # Clear the previous results
    for widget in results_inner_frame.winfo_children():
        widget.destroy()
    if query:
        results = search_api(query)
        # Display the new results
        for result in results:
            # Create a frame to hold the view elements
            result_frame = tk.Frame(results_inner_frame)
            result_frame.pack(side="top", fill="x", pady=(0, 4), padx=(4, 4))
            # Add the result text to the frame
            result_label = tk.Label(result_frame, text=result['title'], wraplength=600)
            result_label.pack(side="left", fill="x", anchor="center")

            # Add the first button to the frame
            if ('tm' in result['jw_entity_id']):
                btn1 = tk.Button(result_frame, text="Movie", command=lambda id=result['id']: on_click(id))
                btn1.pack(side="left", anchor="center")

            # Add the second button to the frame
            if ('ts' in result['jw_entity_id']):
                btn2 = tk.Button(result_frame, text="TV Show", command=lambda id=result['id']: on_click(id, 'show'))
                btn2.pack(side="left", anchor="center")
        # Update the scrollable view
        update_scrollable_view()



# Call the search function whenever the search bar changes
search_var.trace("w", lambda name, index, mode: search())

# Run the main loop
window.mainloop()