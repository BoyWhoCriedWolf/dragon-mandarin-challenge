import React from 'react'


class PhraseInfo extends React.Component {

  render() {

    return (

      <div className="phrase-info text-zinc-700 text-sm">

        <h2 className="font-bold text-lg text-zinc-400">Translation</h2>
        <p>{this.props.obj.english}</p>

      </div>

    )
  }
}

export default PhraseInfo

