import React from 'react'


class FeedbackForm extends React.Component {

  state = {
    input: '',
    isSubmitted: false,
  }

  handleInputChange = (event) => {
    this.setState({input: event.target.value});
  };

  setIsSubmitted = (val) => {
    this.setState({isSubmitted: val});
  }

  handleSubmit = (event) => {
    event.preventDefault();
    fetch('/api/v0/reader/feedback', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        'currentPage': window.location.href,
        'message': this.state.input
      }),
    })
    .then(response => {
      if (response.ok) {
        this.setIsSubmitted(true);
      }
    })
    .catch(error => {

    });
  }

  render() {

    if (this.state.isSubmitted) {
      return (
        <div className="p-3 py-8 border-t border-zinc-200">
          <p>Thanks! Your message has been sent.</p>
        </div>
      )
    } else {
      return (

        <div className="p-3 py-6 border-t border-zinc-200">
          <h2 className="text-lg font-bold text-zinc-400">App feedback</h2>

          <form onSubmit={this.handleSubmit}>
            <textarea
              value={this.state.input}
              onChange={this.handleInputChange}
              className="w-full mt-3 h-32 rounded-md !outline-none border-zinc-400 focus:border-zinc-800 focus:outline-none focus:ring-offset-0 focus:ring-0"
              placeholder="Please report any bugs or share suggestions."></textarea>
            <div className="">
              <button type="submit"
                      className="mt-1 w-full rounded-md px-3 py-2 font-semibold text-zinc-500 bg-zinc-100 shadow-sm hover:bg-zinc-200">Send
              </button>
            </div>
          </form>

        </div>

      )
    }



  }
}

export default FeedbackForm
