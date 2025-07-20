import threading
from llm import plant_analyzer

diagnosis_delay = 5


def start_diagnosis():
    print('start ai diagnosis')
    plant_analyzer.run_plant_diagnosis()
    return

timer = threading.Timer(diagnosis_delay, start_diagnosis)
timer.start()


# 아래 코드는 통합시 포함하지 않음!
timer.join()
