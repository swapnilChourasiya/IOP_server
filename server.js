const express = require('express')
const app = express()
// import {PythonShell} from 'python-shell';
const {PythonShell} = require("python-shell");
// const spawn = require("child_process").spawn;
// const pythonProcess= spawn('python',["./scripts/temp.py",parcel])
let arguments; 
let result;
      
app.use(express.static('public'))
app.use(express.json())


app.post("/",(req,res) => {
   const {parcel} = req.body
   // arguments= parcel
   // console.log(parcel)
  //  console.log(typeof(parcel))
   arguments = JSON.stringify(parcel);
   let options = {
    // pythonPath: "python",
    scriptPath: "./scripts",
    args: arguments
  }
  // const pythonProcess= spawn('python',["./scripts/temp.py",parcel])
   if(!parcel){
      return res.status(400).send({status: 'failed'})
   }
   PythonShell.run('Direct_Method.py', options, function (err,results) { 
      if (err) throw err;
      console.log('this worked fine');
      console.log(results);  
      result = JSON.stringify(results); 
  });
  // pythonProcess.stdout.on('data', (data) => {const dataString= data.toString()
  // console.log(dataString)});
  
  res.status(200).send(result)
})


app.listen(5000, () => {console.log("Server connected on port 5000")})

