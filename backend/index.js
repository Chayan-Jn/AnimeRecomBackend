require('dotenv').config()
const express = require('express')
const {execFile} = require('child_process')
const path = require('path')
const cors = require('cors')

const app = express()
const port = process.env.PORT || 4000;

app.use(cors())
app.get('/recommend',(req,res)=>{
    const animeName = req.query.anime;
    if(!animeName){
        return res.status(200).json({
            Error:"Anime name is required"
        })
    }
    const pythonScriptPath = path.join(__dirname,'..','python','anime_recom.py')
   
    execFile('python', [pythonScriptPath, animeName], (error, stdout, stderr) => {
        if (error) {
            return res.status(500).json({ Error: 'Error executing the Python script', Details: error.message });
        }
        if (stderr) {
            return res.status(500).json({ Error: 'Python script stderr', Details: stderr });
        }

        // Return the result from Python script (which is expected to be a JSON)
        try {
            const result = JSON.parse(stdout);  // Parsing the output into JSON
            res.json(result);
        } catch (parseError) {
            res.status(500).json({ Error: "Error parsing Python script output", Details: parseError.message });
        }
    });
})

app.listen(port,'0.0.0.0',()=>{
    console.log("server listening on port ",port)
})



// Why is '0.0.0.0' important on Render?

//     '0.0.0.0' tells your server to listen on all network interfaces on the assigned port.

//     This enables incoming traffic from the external network to reach your app inside the container or VM.

//     Render forwards incoming HTTP requests to the correct port and IP, so binding to '0.0.0.0' makes your app accessible.
