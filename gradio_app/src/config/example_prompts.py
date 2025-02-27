EXAMPLE_CATEGORIES = {
    "Quick Tasks": [
        {"name": "Play 'Tiny Dancer'", "prompt": "Play 'Tiny Dancer' by Elton John"},
        {"name": "Making Siri Speak", "prompt": "say Shame on YOU! i'm not Siri! but if you want to make me speak, just prompt the agent with 'say' followed by what you want."},
        {"name": "Show My Location", "prompt": "Open Maps and show my current location"},
        {"name": "Mail", "prompt": "Open Mail and quit"}
    ],
    "Multi-Step Tasks": [
        {
            "name": "Calculate 5 times 4",
            "levels": [
                {"level": "Bad", "prompt": "Check what’s four times five"},
                {"level": "Good", "prompt": "Open Calculator and calculate 5 times 4"},
                {"level": "Expert", "prompt": "Open Calculator, click the ‘5’ button, then the multiply button, then the ‘4’ button, then the equals button, and return the result"}
            ]
        },
        {
            "name": "Create a New Note",
            "levels": [
                {"level": "Bad", "prompt": "Make a note"},
                {"level": "Good", "prompt": "Open Notes and create a new note titled 'Meeting Notes'"},
                {"level": "Expert", "prompt": "Open Notes, click the 'New Note' button, type 'Meeting Notes' at the top as a title field, then type the text: 'Discuss project timeline''"}
            ]
        }
    ],
    "Advanced Workflows": [
        {"name": "Organize Files and Send a Message", "prompt": "Open Finder, go to the Documents folder, create a new folder called 'Projects', move all .txt files from Documents into 'Projects'. Then, open Messages, start a new conversation with 'team@example.com', type 'Projects are organized in Documents/Projects', and send it."},
        {"name": "Plan a Meeting with a Map Location", "prompt": "Open Maps, search for 'cafes near Union Square, San Francisco', select the first result, copy its address. Then, open Calendar, create an event titled 'Team Sync' for tomorrow at 9 AM, paste the address into the location field, and invite 'team@example.com'."},
        {"name": "Create a Simple Presentation", "prompt": "Open Keynote, create a new presentation with the 'White' theme, add a title slide with 'Team Update', add a second slide with a bullet list: 'Goal 1: Finish report', 'Goal 2: Plan Q4'. Save it as 'update.key' on the Desktop."}
    ]
}