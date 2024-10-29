import React from 'react'


class ToneColoredString extends React.Component {


  getClassName = (colorBehavior, tone, isSelected) => {

    // The colors for this component come from tailwind (not input.css)
    // We have to hardcode these class names rather than construct them dynamically, or tailwind doesn't
    // pick up the strings when scanning the source
    const classes = []
    if (colorBehavior) {
      if (colorBehavior === 'hover') {
        classes.push({
          // group-hover is a tailwind feature that allows all characters in the word to change color when any one of
          // them is hovered: https://stackoverflow.com/a/65952230
          1:'group-hover:text-tone1',
          2:'group-hover:text-tone2',
          3:'group-hover:text-tone3',
          4:'group-hover:text-tone4',
          5:'group-hover:text-tone5',
        }[tone])
      } else {
        classes.push({
          1:'text-tone1',
          2:'text-tone2',
          3:'text-tone3',
          4:'text-tone4',
          5:'text-tone5',
        }[tone])
      }
    }

    if (isSelected) {
      classes.push('bg-red-500')
    }

    return classes.join(' ')

  }

  render() {
    // colorBehavior should be true (always color), 'hover' (color only on hover), or false (never color)
    const {chars, tones, selectedChar=0, colorBehavior = true} = this.props;

    return (
      <span className="group">
      {
        Array.from(chars).map((char, i) => (
          <span
            key={i}
            className={this.getClassName(colorBehavior, tones[i], selectedChar === 0 ? false : i + 1 === selectedChar)}
          >
          {char}
        </span>
        ))
      }
      </span>
    )
  }
}

export default ToneColoredString
