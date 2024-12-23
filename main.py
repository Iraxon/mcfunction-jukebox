import enum
import mido
from tkinter import Tk, filedialog
import os
import pyperclip


class Edition(enum.Enum):
    JAVA = "JAVA"
    BEDROCK = "BEDROCK"


def right_clicks_to_factor(rc):
    """
    Converts note-blockr-right-clicks
    into pitch multipliers for use withdraw

    /playsound
    """

    return 2 ** ((rc - 12) / 12)  # Formula from minecraft.wiki


def pre_boilerplate(name, edition):
    """
    Returns the boilerplate commands
    that precede the actual note commands
    """
    return (
        f"scoreboard objectives add MCFJ.Tick.{name} dummy\n"
        f"scoreboard players add @a MCFJ.Tick.{name} 0\n"
        f"execute as @a[tag=MCFJ.{name}] at @s "
        f"run {'stopsound @s music' if edition == Edition.JAVA else 'music stop'}\n"
    )


def post_boilerplate(name, next_tick):
    """
    Returns the boilerplate commands
    that go after the notes
    """
    return (
        f"execute as @a[tag=MCFJ.{name}] at @s run "
        f"scoreboard players add @s MCFJ.Tick.{name} 1"
        "\n"
        f"execute as @a[tag=MCFJ.{name}] at @s "
        f"if score @s MCFJ.Tick.{name} matches {next_tick}.. "
        f"run scoreboard players reset @s MCFJ.Tick.{name}"
        "\n"
        f"execute as @a[tag=!MCFJ.{name}] at @s run "
        f"scoreboard players reset @s MCFJ.Tick.{name}"
        "\n"
    )


JAVA_SOUND = "minecraft:block.note_block.bass"
BK_SOUND = "note.bass"


def get_filename_without_extension(path):
    return os.path.splitext(os.path.basename(path))[0]


def catalog_notes(midi):
    """
    Returns a tuple of
    (time <MC ticks>, pitch <MC noteblock right-clicks>)
    tuples from a given mido.MidiFile object

    AND

    the time in MC ticks of track end
    """

    abs_time = 0
    tempo = 0

    notes_on = []

    end = 0

    for track in midi.tracks:
        abs_time = 0
        for msg in track:
            abs_time += mido.tick2second(msg.time, midi.ticks_per_beat, tempo)

            if msg.type == "set_tempo":
                tempo = msg.tempo
            elif msg.type == "note_on":
                notes_on.append(
                    (
                        round(abs_time * 20),
                        (msg.note - 54) % (78 - 54) if msg.note != 78 else 78 - 54,
                    )
                )
            elif msg.type == "end_of_track":
                end = round(abs_time * 20)
    return tuple(notes_on), end


def midi_to_mcfunction(src, edition=Edition.JAVA):
    """
    Accepts file path of a .MID file
    Returns mcfunction music
    """

    midi = mido.MidiFile(src)
    midi.ticks_per_beat = 480

    TITLE = "_".join(get_filename_without_extension(src).split())

    NOTES, END = catalog_notes(midi)

    return (
        pre_boilerplate(TITLE, edition)
        + "".join(
            tuple(
                f"execute as @a at @s if entity @s[tag=MCFJ.{TITLE}] "
                f"if score @s MCFJ.Tick.{TITLE} "
                f"matches {note[0]} "
                f"run playsound "
                f"{ {Edition.JAVA: JAVA_SOUND, Edition.BEDROCK: BK_SOUND}[edition] } "
                f"{ {Edition.JAVA: 'voice ', Edition.BEDROCK: ''}[edition] }"
                f"@s ~ ~ ~ 1.0 {round(right_clicks_to_factor(note[1]),6)}\n"
                for note in NOTES
            )
        )
        + post_boilerplate(TITLE, END)
    )


if __name__ == "__main__":
    edition = Edition.JAVA

    root = Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("MIDI Files", "*.mid *.midi")])

    TRANSLATION = midi_to_mcfunction(file_path)

    print(TRANSLATION)

    pyperclip.copy(TRANSLATION)

    print("\n\n Translation copied")
