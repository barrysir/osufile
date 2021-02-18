def default_filename(osu):
    "Get the default filename of an OsuFile object: '{artist} - {title} ({creator}) [{difficulty}].osu'"
    # use non-unicode values for the artist and title
    return f"{osu['Metadata']['Artist']} - {osu['Metadata']['Title']} ({osu['Metadata']['Creator']}) [{osu['Metadata']['Version']}].osu"