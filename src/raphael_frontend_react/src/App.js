import './App.css';
import { useState } from "react";

const conf = {
  baseUrl: 'https://raphael.fullfact.org/api',
  defaultHeaders: {
    Accept: "application/json",
    "Content-Type": "application/json;charset=UTF-8"
  }
}

function App() {
  const params = new URL(document.location).searchParams;
  const query = params.get("q");
  const [searchCode, setSearchCode] = useState(query);
  const [userAuth, setUserAuth] = useState(null);
  const [claims, setClaims] = useState(null);
  const [transcript, setTranscript] = useState(null);
  const [status, setStatus] = useState(null);
  const [recentTranscripts, setRecentTranscripts] = useState(null);

  if(userAuth) {
    if(searchCode) {
      if(!transcript) {
        getTranscript(searchCode)
        getStatus(searchCode)
        getClaims(searchCode)
      }
    } else if(!recentTranscripts) {
      getRecentTranscripts();
    }
    
  }


  function login(e) {
    e.preventDefault();
    const form = e.currentTarget.elements;
    const username =  form.username.value;
    const password =  form.password.value;
    setUserAuth(btoa(username + ":" + password));
  }

  function handleSearchCode(e, code) {
    e.preventDefault();
    setSearchCode(code);
    window.history.pushState({}, '', '?q=' + code);
    getTranscript(code);

  }

  function createTranscript(e) {
    e.preventDefault();
    const youtubeId = e.currentTarget.elements.q.value;
    setSearchCode(youtubeId)
    const url = conf.baseUrl + '/transcripts/';
    fetch(url, {
      method: "POST",
      headers: {
        ...conf.defaultHeaders,
        'Authorization' : 'Basic ' + userAuth
      },
      body: JSON.stringify({
        id: youtubeId
      }),
    })
    .then((response) => response.json())
    .then((data) => {
      setTranscript(data);
      window.history.pushState({}, '', '?q=' + youtubeId);
      getRecentTranscripts();
    });
    /*
    setTranscript({
      title: 'Common and Accessible Herbs for Stress and Anxiety | Plant-Based | Well+Good',
      id: 'Z0_ulRoJFLg',
    });
    */
    
  }
  
  function getTranscript(youtubeId) {
    const url = conf.baseUrl + '/transcripts/' + youtubeId;
    fetch(url, {
      headers: {
        ...conf.defaultHeaders,
        'Authorization' : 'Basic ' + userAuth
      }
    })
    .then((response) => response.json())
    .then((data) => {
      setTranscript(data);
      window.history.pushState({}, '', '?q=' + youtubeId);
      getClaims(youtubeId)
      getStatus(youtubeId)
    });
    /*
      setTranscript({
        title: 'Common and Accessible Herbs for Stress and Anxiety | Plant-Based | Well+Good',
        id: 'Z0_ulRoJFLg',
      });
    */

    
  }

  function getClaims(youtubeId) {
    const url = conf.baseUrl + '/inferred_claims/' + youtubeId;
    fetch(url, {
      headers: {
        ...conf.defaultHeaders,
        'Authorization' : 'Basic ' + userAuth
      }
    })
    .then((response) => response.json())
    .then((data) => {
      
      setClaims(data.map(claim => ({
        ...claim,
        time: Math.floor(claim.offset_ms/1000)
      })));
      
    });
    /*
    setClaims([
      {claim: 'this is a claim', time: '34'}
    ])
    */
    
  }

  function getStatus(youtubeId) {
    const url = conf.baseUrl + '/inferred_claims/' + youtubeId + '/status';
    fetch(url, {
      headers: {
        ...conf.defaultHeaders,
        'Authorization' : 'Basic ' + userAuth
      }
    })
    .then((response) => response.json())
    .then((data) => {
      setStatus(data.status);
    });
    /*
    setStatus('completed');
    */
    
  }

  function getRecentTranscripts() {

    const url = conf.baseUrl + '/transcripts/';
    fetch(url, {
      headers: {
        ...conf.defaultHeaders,
        'Authorization' : 'Basic ' + userAuth
      }
    })
    .then((response) => response.json())
    .then((data) => {
      setRecentTranscripts(data)
    });
    
    /*
    setRecentTranscripts([
      {title: 'Common and Accessible Herbs for Stress and Anxiety | Plant-Based | Well+Good', id: "o9AEPKn4MMI"},
      {title: 'The BEST Natural Antibiotic Drink (Home Remedy Formula) | 100% natural | TURMERIC Benefits', id: "K1EbMbXpjs0"},
      {title: 'How To Lighten Your Skin | Skin Whitening Home Remedies', id: "Z0_ulRoJFLg"},
      {title: 'Fast Home Remedies to Lower BLOOD PRESSURE', id: "xOsAwyH2lLc"},
      {title: 'Curcumin (Turmeric)– A Natural Way To Fight Depression', id: "Hrv01WYjqtU"},
      {title: 'Benefits of Castor Oil by Barbara O’Neill', id: "2508ZPcN9PM"},
      {title: 'How to Lower Your Blood Pressure in 5 minutes Using Only 1 Onion', id: "Ih5cz-Qwa6U"},
      {title: 'When I Held My Newborn Granddaughter In My Arms, Realized I Couldn’t See Her Face', id: "FU7r3yGjjWc"},
      {title: 'Aluminum and Mercury Cool Science Experiment', id: "ZVkpQKRgHvU"}
    ]);
    */
    
  }

  function clearTranscript(e) {
    setSearchCode(null)
    window.history.pushState({}, '', '?q=');
    e.preventDefault();
    setClaims(null);
    setTranscript(null);
    setStatus(null);
    getRecentTranscripts();
  }


  return (
    <div className="App">
      {!userAuth ? (
        <div>
          <form className="form" onSubmit={login}>
            <div style={{textAlign: 'center ', margin: '107px 0' }}>
                <input type="text" style={{width: '500px', margin: '12px auto' }} className="form-control" placeholder="Username" id="username" name="username" />
                <input type="text" style={{width: '500px', margin: '12px auto 32px auto' }} className="form-control" placeholder="Password" id="passowrd" name="password" />
                <button className="btn btn-brand-neutral-black" type="submit">Login</button>
            </div>
          </form>
        </div>
      ): (
        <div>
          <h2>Find health misinformation in YouTube videos</h2>
          <form className="form" onSubmit={createTranscript}>
            <div className="input-group">
                <input type="text" className="form-control" placeholder="Enter a YouTube URL" name="q" aria-label="Search" style={{marginRight: '12px'}} />
                  <button type="submit" className="btn btn-brand-neutral-black" >Analyse</button>
            </div>
          </form>
          {transcript && searchCode?.length ? (
            <div>
              <a href="/" onClick={clearTranscript} style={{marginTop: '12px', display: 'inline-block'}}>Back to recent searches</a>
              <h4>Claims for '{transcript.title || searchCode}'.</h4>
              {status === 'error' && (
                <p>Something went wrong when trying to find claims.</p>
              )}
              {status === 'processing' && (
                <p>This video is currently being processed and may take a couple of minutes to find claims.</p>
              )}
              {status === 'completed' && (
                <div>
                {claims.length ? (
                  <ul>
                  {claims.map(sr => (
                  <li><a href={"https://www.youtube.com/watch?v="+transcript.id+"&t="+sr.time}>{sr.claim}</a></li>
                  ))}
                </ul>
                ): (
                  <p>No claims found</p>
                )}
                </div>
              )}
            </div>
          ) : (
            <div>
              <h6>History</h6>
              <ul>
                {recentTranscripts?.map(tr => (
                <li key={tr.id}><a href={"?q="+tr.id} onClick={(e) => { handleSearchCode(e, tr.id)}}>{tr.title} ({tr.id})</a></li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
