import React from 'react';
import ReactDOM from 'react-dom';
import Reader from "./Reader";


const articlePk = document.getElementById('article-pk').textContent;

ReactDOM.render(
  <React.StrictMode>
    <Reader articlePk={articlePk}/>
  </React.StrictMode>,
  document.getElementById('reader')
);

