const express = require('express')
const app = express()
const {PythonShell} = require("python-shell");



let arguments;
let DMResults;
app.use(express.static('public')) 
app.use(express.json())
 
//post request for direct flow method
app.post("/dmMethod", (req,res) => {
   const {parcel} = req.body
   arguments = JSON.stringify(parcel); 

   let options = { 
    scriptPath: "./scripts",
    args: arguments 
   }   

   if(!parcel){ return res.status(400).send({status: 'failed'})}
   PythonShell.run('Direct_Method.py', options, function (err,results) { 
    if (err) throw err; 
    console.log('this worked fine for directMethod1'); 
    console.log(results);  
    DMResults = JSON.stringify(results);  
    res.status(201).send(DMResults)
  });
})

app.post("/dmMethod2", (req,res) => {

   const {parcel} = req.body
   arguments = JSON.stringify(parcel); 

   let options = { 
    scriptPath: "./scripts",
    args: arguments 
   }   

   if(!parcel){ return res.status(400).send({status: 'failed'})}
   PythonShell.run('Direct_Method2.py', options, function (err,results) { 
    if (err) throw err; 
    console.log('this worked fine for DirectMethod2:'); 
    console.log(results);  
    DMResults = JSON.stringify(results);  
    res.status(201).send(DMResults)
  });
})


app.listen(5000, () => {console.log("Server connected on port 5000")})

