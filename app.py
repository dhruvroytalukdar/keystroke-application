import tkinter as tk
import time
import os
import pandas as pd

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Keystroke Dynamics Application")
        self.geometry("600x400")

        # User name
        self.user_name = None
        # Current Session
        self.session = None
        # current time to calculate latency
        self.curr_time = None

        self.press_time = None
        self.release_time = None
        self.prev_press_time = None
        self.prev_release_time = None
        self.index = 0
        self.wrong = 0
        self.curr_key = None

        # Read and store the sentences to be typed
        self.dataset = []
        with open("sentences.txt", "r") as file:
            sentences = file.readlines()
            for sentence in sentences:
                print(sentence.strip())
                if sentence.strip()[-1] == "\n":
                    self.dataset.append(sentence.strip()[:-1])
                else:
                    self.dataset.append(sentence.strip())
        
        # Index of the current sentence to be typed
        self.sentence_index = 0
        # Status of the sentence the user is typing
        self.typed_sentence = ""


        title = tk.Label(self, text="Keystroke Dynamics Application", font=("Helvetica", 24))
        title.pack(pady=10)

        # Enter username prompt
        self.label = tk.Label(self, text="Enter your username:", font=("Helvetica", 18))
        self.label.pack(pady=10)

        # Create a textfield to enter username
        self.username_entry = tk.Entry(self, font=("Helvetica", 18))
        self.username_entry.pack(pady=10)

        # Create a button to get the text from the textfield
        self.username_button = tk.Button(self, text="Submit", command=self.get_username, font=("Helvetica", 18))
        self.username_button.pack(pady=10)

        self.map = {
            "key_pressed": [],
            "hold_latency": [],
            "inter_key_latency": [],
            "press_latency": [],
            "release_latency": [],
            "timestamp": [],
            "missed_keys": 0,
        }

        self.typing_map = []


    def create_user_directory(self, directory_name):
        if not os.path.exists(directory_name):
            os.makedirs(directory_name)

    def get_username(self):
        if self.username_entry.get() == "":
            return
        self.user_name = self.username_entry.get()
        self.session = time.time()
        # create a new directory with username
        self.create_user_directory(self.user_name)
        # change screen to another screen
        self.change_screen()
    
    def change_screen(self):
        # Remove username and username button
        self.username_entry.pack_forget()
        self.username_button.pack_forget()
        self.label.pack_forget()

        # Sentence to be typed
        self.sentence_label = tk.Label(self, text=self.dataset[self.sentence_index], font=("Helvetica", 18))
        self.sentence_label.pack(pady=10)

        # Display the status of the sentence user is currently typing
        self.typing_label = tk.Label(self, text=self.typed_sentence,font=("Helvetica", 18), foreground="green")
        self.typing_label.pack(pady=10)

        # Create a button to get the text from the textfield
        self.start_button = tk.Button(self, text="Start Typing", command=self.start_typing, font=("Helvetica", 18))
        self.start_button.pack(pady=10)
    
    def start_typing(self):
        # Remove start button
        self.start_button.pack_forget() 

        # Add next button in disabled state
        self.next_button = tk.Button(self, text="Next", command=self.next_sentence, font=("Helvetica", 18), state="disabled")        
        self.next_button.pack(pady=10)

        self.bind("<Key>", self.key_pressed)
        self.bind("<KeyRelease>", self.key_released)
    
    def next_sentence(self):
        self.sentence_index += 1
        if self.sentence_index < len(self.dataset):
            self.store_typed_results()
            self.typing_map = []
            self.map = {
                "key_pressed": [],
                "hold_latency": [],
                "inter_key_latency": [],
                "press_latency": [],
                "release_latency": [],
                "timestamp": [],
                "missed_keys": 0,
            }
            self.typed_sentence = ""
            self.next_button.pack_forget()
            self.change_text()
            self.update_typed_sentence()
            self.start_button.pack(pady=10)
            self.index = 0
            self.press_time = None
            self.release_time = None
            self.wrong = 0
            self.unbind("<Key>")
            self.unbind("<KeyRelease>")
        else:
            self.store_typed_results()
            self.destroy()

    def change_text(self):
        self.sentence_label.config(text=self.dataset[self.sentence_index])

    def update_typed_sentence(self):
        # change the color of the part of label that has been typed correctly
        self.typing_label.config(text=self.typed_sentence)

    def key_pressed(self, event):
        if event.keysym != "BackSpace":
            if self.curr_key == event.keysym:
                return
            print("current ",event.keysym, self.curr_key)
            if event.char == self.dataset[self.sentence_index][self.index]:
                if self.curr_key == None:
                    self.curr_key = event.keysym
                    self.press_time = time.time()
                print(event.keysym, "pressed")
            else:
                self.wrong += 1
                print("Wrong key pressed", self.wrong)

    def store_typed_results(self):
        RELEASE = 2
        PRESS = 1
        CHAR = 0
        for i in range(len(self.typing_map)-1):
            self.map["key_pressed"].append(self.typing_map[i][CHAR])
            self.map["hold_latency"].append(self.typing_map[i][RELEASE] - self.typing_map[i][PRESS])
            self.map["inter_key_latency"].append(self.typing_map[i+1][PRESS] - self.typing_map[i][RELEASE])
            self.map["press_latency"].append(self.typing_map[i+1][PRESS] - self.typing_map[i][PRESS])
            self.map["release_latency"].append(self.typing_map[i+1][RELEASE] - self.typing_map[i][RELEASE])
            self.map["timestamp"].append(self.typing_map[i][PRESS])
            self.map["missed_keys"] = self.wrong

        i = len(self.typing_map)-1
        self.map["key_pressed"].append(self.typing_map[i][CHAR])
        self.map["hold_latency"].append(self.typing_map[i][RELEASE] - self.typing_map[i][PRESS])
        self.map["press_latency"].append(0)
        self.map["inter_key_latency"].append(0)
        self.map["release_latency"].append(0)
        self.map["timestamp"].append(self.typing_map[i][PRESS])
        self.map["missed_keys"] = self.wrong


        self.create_user_directory(f"{self.user_name}/{str(int(self.session))}")
        # store the result as pandas dataframe
        df = pd.DataFrame(self.map)
        df.to_csv(f"{self.user_name}/{str(int(self.session))}/{self.sentence_index}.csv", index=False)

    
    def key_released(self, event):
        # if the character is a to z or A to Z
        if event.keysym.isalpha():
            # if there is a backspace
            if event.keysym == "BackSpace":
                # return
                self.index -= 1
                self.typed_sentence = self.typed_sentence[:-1]
                if self.typed_sentence != self.dataset[self.sentence_index]:
                    self.next_button.config(state="disabled")
            else:
                if self.curr_key == None:
                    return
                self.index += 1
                self.typed_sentence += event.char
                if event.char == self.dataset[self.sentence_index][self.index-1]:
                    self.release_time = time.time()
                    self.curr_key = None
                    self.typing_map.append((event.keysym, self.press_time, self.release_time))
                    print(event.keysym, "released")
                    print("Latency: ", self.release_time - self.press_time)
                if self.typed_sentence == self.dataset[self.sentence_index]:
                    self.next_button.config(state="normal")
        
        self.update_typed_sentence()

if __name__ == "__main__":
    app = App()
    app.mainloop()