import storage
import valid
import scheme
import copy

FUNCS = copy.deepcopy(scheme.SHEME_ADD)
FUNCS.pop("computed_scores")

def get_validators(tags_validators: list) -> list:
    return [valid.VALIDATORS[tag] for tag in tags_validators]
    



def loop_input(text, funcs_list):
    "Запрос ввода параметров и валидацией"
    
    while True:
        value = input(text)
        for func in funcs_list:
            if func(value) is False:
                break
        else:
            break      
    return value

def request_all_scores() -> dict:
    """Запрашивает у пользователя все поля фильма и возвращает общий словарь."""
    movie = {}

    for section_name, section_fields in FUNCS.items():
        section = {}

        print(f'\n--- {section_name} ---')

        for feature, field_settings in section_fields.items():
            tags_validators, type_func = field_settings
            funcs =  get_validators(tags_validators)
            answer = loop_input(
                text=f'>> {feature}: ',
                funcs_list=funcs
                            )
            section[feature] = type_func(answer)

        movie[section_name] = section

    return movie
