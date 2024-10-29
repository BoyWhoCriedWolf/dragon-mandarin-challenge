import React from 'react'

class ReaderOptions extends React.Component {

    handlePinyinChange = (e) => {
        this.props.setShowPinyin(e.currentTarget.checked);
    }

    handleToneColorsChange = (e) => {
        this.props.setShowToneColors(e.currentTarget.checked);
    }

    render() {

        const { showPinyin, showToneColors } = this.props.options;

        return (


            <div className="reader-options pb-3">
                <div className="mt-1 flex items-center">
                    <input type="checkbox" id="option-pinyin" onChange={this.handlePinyinChange} checked={showPinyin} />
                    &nbsp;
                    <label htmlFor="option-pinyin">Pinyin</label>
                </div>
                <div className="mt-1 flex items-center">
                    <input type="checkbox" id="option-tone-colors" onChange={this.handleToneColorsChange} checked={showToneColors} />
                    &nbsp;
                    <label htmlFor="option-tone-colors">Tone colours</label>
                </div>
            </div>

        )

    }
}

export default ReaderOptions


