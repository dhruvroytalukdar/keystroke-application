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
        self.press_index = 0
        self.release_index = 0
        self.wrong = 0
        self.curr_key = None

        # Read and store the sentences to be typed
        self.dataset = []
        with open("sentences.txt", "r") as file:
            sentences = file.readlines()
            for sentence in sentences:
                # print(sentence.strip())
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

        self.press_map = {}
        self.release_map = {}

    def create_user_directory(self, directory_name):
        if not os.path.exists(directory_name):
            os.makedirs(directory_name)

    def get_username(self):
        if self.username_entry.get() == "":
            return
        self.user_name = self.username_entry.get()
        self.session = time.time()
        # create a new directory with username
        self.create_user_directory(f"user_{self.user_name}")
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
        self.store_typed_results()
        if self.sentence_index < len(self.dataset):
            self.press_map = {}
            self.release_map = {}
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
            self.order_sequence = list(self.dataset[self.sentence_index])
            self.update_typed_sentence()
            self.start_button.pack(pady=10)
            self.press_index = 0
            self.release_index = 0
            self.press_time = None
            self.release_time = None
            self.wrong = 0
            self.unbind("<Key>")
            self.unbind("<KeyRelease>")
        else:
            self.get_rand_bit_string()
            self.destroy()

    def get_rand_bit_string(self):
        scale = 1_000_000_000_000
        bits_range = 2**32
        path = f"user_{self.user_name}/{str(int(self.session))}"
        write_result = []
        for i in range(1, 6):
            keystroke_data = pd.read_csv(f"{path}/{i}.csv")
            result = None
            for i in range(len(keystroke_data)):
                first_row = keystroke_data.iloc[i]
                press_latency = str(format(int(first_row['press_latency'] * scale)%bits_range, '032b'))
                hold_latency = str(format(int(first_row['hold_latency'] * scale)%bits_range, '032b'))
                inter_key_latency = str(format(int(first_row['inter_key_latency'] * scale)%bits_range, '032b'))
                release_latency = str(format(int(first_row['release_latency'] * scale)%bits_range, '032b'))
                final_bit_string = press_latency + hold_latency + inter_key_latency + release_latency
                if result is None:
                    result = final_bit_string
                else:
                    # xor the bit strings
                    result = ''.join('1' if a != b else '0' for a, b in zip(result, final_bit_string))
            write_result.append(result)
        with open(f"{path}/bit_strings.txt", 'w') as f:
            for item in write_result:
                f.write("%s\n" % item)

    def change_text(self):
        self.sentence_label.config(text=self.dataset[self.sentence_index])

    def update_typed_sentence(self):
        # change the color of the part of label that has been typed correctly
        display_text = ""
        for i in range(len(self.typed_sentence)):
            if self.typed_sentence[i] == " ":
                display_text += "-"
            else:
                display_text += self.typed_sentence[i]
        self.typing_label.config(text=display_text)

    def key_pressed(self, event):
        if event.keysym != "BackSpace":
            if event.char == self.dataset[self.sentence_index][self.press_index]:
                self.press_index += 1
                self.press_time = time.time()
                self.press_map[self.press_index-1] = (event.keysym, self.press_time)
                self.curr_key = event.keysym
                self.typed_sentence += event.char
                # print(event.keysym, "pressed")
            else:
                self.wrong += 1
                # print("Wrong key pressed", self.wrong)
        self.update_typed_sentence()
    
    def key_released(self, event):
        if event.keysym.isalpha():
            # somehow determine the key released is correct or not
            if self.release_index < self.press_index and event.keysym == self.press_map[self.release_index][0]:
                self.release_index += 1
                self.release_time = time.time()
                self.release_map[self.release_index-1] = (event.keysym, self.release_time)
                self.curr_key = None
                # print(event.keysym, "released")
                # print("Latency: ", self.release_time - self.press_time)

            if self.typed_sentence == self.dataset[self.sentence_index]:
                self.next_button.config(state="normal")

    def abs_func(self, x):
        if x < 0:
            return -1*x
        return x

    def store_typed_results(self):
        RELEASE = 1
        PRESS = 1
        CHAR = 0

        for i in range(len(self.press_map)-1):
            self.map["key_pressed"].append(self.press_map[i][CHAR])
            self.map["hold_latency"].append(self.abs_func(self.release_map[i][RELEASE] - self.press_map[i][PRESS]))
            self.map["inter_key_latency"].append(self.abs_func(self.press_map[i+1][PRESS] - self.release_map[i][RELEASE]))
            self.map["press_latency"].append(self.abs_func(self.press_map[i+1][PRESS] - self.press_map[i][PRESS]))
            self.map["release_latency"].append(self.abs_func(self.release_map[i+1][RELEASE] - self.release_map[i][RELEASE]))
            self.map["timestamp"].append(self.abs_func(self.press_map[i][PRESS]))
            self.map["missed_keys"] = self.wrong

        i = len(self.press_map)-1
        self.map["key_pressed"].append(self.press_map[i][CHAR])
        self.map["hold_latency"].append(self.abs_func(self.release_map[i][RELEASE] - self.press_map[i][PRESS]))
        self.map["press_latency"].append(0)
        self.map["inter_key_latency"].append(0)
        self.map["release_latency"].append(0)
        self.map["timestamp"].append(self.abs_func(self.press_map[i][PRESS]))
        self.map["missed_keys"] = self.wrong


        self.create_user_directory(f"user_{self.user_name}/{str(int(self.session))}")
        df = pd.DataFrame(self.map)
        df.to_csv(f"user_{self.user_name}/{str(int(self.session))}/{self.sentence_index}.csv", index=False)


if __name__ == "__main__":
    app = App()
    app.mainloop()