# Updated events filtering logic

events = [...]  # Your existing list of events

# Filter out events that are named "HAPPENING NOW"
filtered_events = [event for event in events if event.name != "HAPPENING NOW"]

# Add the filtered events to the events list
# your existing logic to add them to the events list goes here...