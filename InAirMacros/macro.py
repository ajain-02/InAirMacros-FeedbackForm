from tkinter import *
import json
import queue
import sounddevice as sd
import vosk
from tkinter import *
import string
vosk.SetLogLevel(-1)
import sys
import os
import pyautogui
import threading


class Ask_KITA(threading.Thread):
    def __init__(self) -> None:
        super(Ask_KITA, self).__init__()
        # self.daemon = True
        self.paused = True  # Start out paused.
        self.state = threading.Condition()
        self.f = open("generated.txt" , "w")
        self.q = queue.Queue()
        device_info = sd.query_devices(kind='input')
        self.samplerate = int(device_info['default_samplerate'])
        model = vosk.Model("model")
        self.recogniser = vosk.KaldiRecognizer(model, self.samplerate)
        self.previous_line = ""
        self.previous_length = 0

    def run(self):
        self.resume()
        with sd.RawInputStream(samplerate=self.samplerate, blocksize=8000, device=None, dtype='int16', channels=1,
                               callback=self.callback):
            while True:
                with self.state:
                    if self.paused:
                        self.state.wait()  # Block execution until notified.
                        with self.q.mutex:
                            self.q.queue.clear()
                # Do stuff...
                
                var = self.write_current_phrase()

    def pause(self):
        with self.state:
            self.paused = True  # Block self.

    def resume(self):
        with self.state:
            self.paused = False
            self.state.notify()  # Unblock self if waiting.

    def write_current_phrase(self):
        d = self._get_current_phrase_dict()
        (key, value), = d.items()
        if value and (value != self.previous_line or key == 'text'):
            self._write(d)
            self.previous_line = value
        return value
    def _get_current_phrase_dict(self):
        data = self.q.get()
        if self.recogniser.AcceptWaveform(data):
            d = json.loads(self.recogniser.Result())
        else:
            d = json.loads(self.recogniser.PartialResult())
        return d

    def _write(self, phrase):
        pyautogui.press('backspace', presses=self.previous_length)
        if 'text' in phrase:
            pyautogui.typewrite(phrase['text'] + '\n')
            self.previous_length = 0
        else:
            pyautogui.typewrite(phrase['partial'])
            self.previous_length = len(phrase['partial'])

    def callback(self, indata, frames: int, time, status) -> None:
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
            sys.stdout.flush()
        self.q.put(bytes(indata))

    def _get_model_path(self) -> str:
        """Returns path of the model
          :return: model path
          :rtype: str
          """
        full_path = os.path.realpath(__file__)
        file_dir = os.path.dirname(full_path)
        model_path = os.path.join(file_dir, 'model')
        return model_path

    def speech_to_text(self):
        if self.ask_kita_running and not self.ask_kita_is_paused:
            print("Pause ask KITA")
            self.ask_kita_is_paused = True
            self.kita.pause()
        elif self.ask_kita_is_paused:
            print("Resume ask KITA")
            self.ask_kita_is_paused = False
            self.kita.resume()
        else:
            print("Start ask KITA")
            self.kita.start()
            self.ask_kita_running = True

macros = json.load(open('data.json'))
alphabet = list(string.ascii_lowercase)


def saveJson():
    with open('data.json','w') as f:
        f.write(json.dumps(macros))


window = Tk()
window.geometry("1000x700")
window.configure(bg="white")


########################################################################################################################
frm_showTasks = Frame(window)

chosenTask = None
questions  = None
def pickTask():
    global chosenTask,questions

    task = entr_task.get()
    if task not in macros:
        lbl_error = Label(frm_showTasks, text = 'no such task' , fg= 'red')
        lbl_error.pack()
    else:
        frm_showQuestions.pack()
        frm_showTasks.pack_forget()
        chosenTask = task

tasksVariable = StringVar()
lbl_tasks = Label(frm_showTasks,textvariable = tasksVariable)
tasksVariable.set('\n'.join([key for key in macros]))
entr_task = Entry(frm_showTasks)
btn_pickTask = Button(frm_showTasks ,command=pickTask,text = 'pick')

lbl_tasks.pack()
entr_task.pack()
btn_pickTask.pack()
########################################################################################################################
frm_showQuestions = Frame(window)
questions = None
def sumbit():
    global questions
    if questions == None:
        questions = macros[chosenTask].copy()
        quest = questions.pop()
        questionVariable.set(quest)
    elif questions == []:
        questions = None
        frm_showQuestions.pack_forget()
        frm_main.pack()
    else:
        quest = questions.pop()
        questionVariable.set(quest)

questionVariable = StringVar()
questionVariable.set('click sumbit to show questions')
lbl_question  = Label(frm_showQuestions ,textvariable=questionVariable)
txt_answer = Text(frm_showQuestions)
btn_sumbit = Button(frm_showQuestions,command=sumbit,text = 'submit')

lbl_question.pack()
txt_answer.pack()
btn_sumbit.pack()
########################################################################################################################

frm_addTask = Frame(window)
newTask = None
def addTask():
    global newTask
    newTask = entr_addTask.get()
    macros[newTask] = []
    saveJson()
    frm_addTask.pack_forget()
    frm_addQuestion.pack()

entr_addTask = Entry(frm_addTask)
btn_addTask = Button(frm_addTask,command = addTask,text = 'add')

entr_addTask.pack()
btn_addTask.pack()
########################################################################################################################
frm_addQuestion = Frame(window)
def addQuestion():
    macros[newTask] += [txt_question.get("1.0",END)]
def submitQuestion():
    saveJson()
    frm_addQuestion.pack_forget()
    frm_main.pack()
txt_question = Text(frm_addQuestion)
btn_addQuestion = Button(frm_addQuestion , text = 'add' , command = addQuestion)
btn_submitQuestion = Button(frm_addQuestion, text = 'submit' , command = submitQuestion)

txt_question.pack()
btn_addQuestion.pack()
btn_submitQuestion.pack()


########################################################################################################################

#main Frame
def selectCommand():
    frm_main.pack_forget()
    frm_showTasks.pack()
def addCommand():
    frm_main.forget()
    frm_addTask.pack()
frm_main = Frame(window)

btn_add = Button(text="add macro",master = frm_main,command = addCommand,bg= "green")
btn_help = Button(text="help",master = frm_main,bg = "green")
btn_edit = Button(text="edit",master = frm_main,bg = "green")
btn_select = Button(text="select macro",master = frm_main,command = selectCommand,bg = "green")

btn_add.pack()
btn_select.pack()
btn_edit.pack()
btn_help.pack()

frm_main.configure(bg='white')
########################################################################################################################

t2 = Ask_KITA()
t2.start()
#t2.pause()

frm_main.pack(side=TOP)
window.mainloop()

