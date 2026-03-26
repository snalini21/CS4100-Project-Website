def collapse_repeats_by_line(input_file, output_file):
    try:
        with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
            for line in f_in:
                tokens = line.split()

                if not tokens:
                    f_out.write("\n")
                    continue

                collapsed = [tokens[0]]
                for i in range(1, len(tokens)):
                    if tokens[i] != tokens[i - 1]:
                        collapsed.append(tokens[i])

                f_out.write(" ".join(collapsed) + "\n")

        print(f"Done! Cleaned file saved as: {output_file}")

    except FileNotFoundError:
        print("Error: The input file was not found.")


# Usage
collapse_repeats_by_line('models/data/chord_bases.txt',
                         'models/data/chord_bases_no_repeats.txt')