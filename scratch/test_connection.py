from pathlib import Path

TO_PIPE = Path("/tmp/audacity_script_pipe.to.1000")
FROM_PIPE = Path("/tmp/audacity_script_pipe.from.1000")

print("Opening write pipe...")
with TO_PIPE.open("w") as to_pipe:
    print("Writing command...")
    to_pipe.write("Help:\n")
    to_pipe.flush()

print("Write complete.")

print("Opening read pipe...")
with FROM_PIPE.open("r") as from_pipe:
    print("Read pipe opened.")

    while True:
        line = from_pipe.readline()
        print(repr(line))
        if not line:
            print("EOF")
            break
