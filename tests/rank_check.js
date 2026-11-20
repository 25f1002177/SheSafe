// Runs the page's real distanceMeters + updateNearestVendor against fixture vendors.
const fs=require('fs');const src=fs.readFileSync('app/templates/explore_legacy.html','utf8');
const grab=n=>{const i=src.indexOf('function '+n);let d=0,j=src.indexOf('{',i);for(let k=j;;k++){if(src[k]=='{')d++;if(src[k]=='}'&&--d==0)return src.slice(i,k+1);}};
let out;const renderVendorList=l=>{out=l.map(v=>v.name+' '+(v.dist/1000).toFixed(0)+'km')};
const document={getElementById:()=>({innerHTML:''})};
eval(grab('distanceMeters')+';'+grab('updateNearestVendor')+';global.u=updateNearestVendor');
const V=[['Real Kolkata',22.57,88.36],['Real Kharagpur',22.31,87.31],['Real Far Chennai',13.08,80.27]].map(([name,lat,lng])=>({name,lat,lng}));
for(const [n,p] of [['KGP',{lat:22.3149,lng:87.3105}],['Kolkata',{lat:22.5726,lng:88.3639}],['Mumbai',{lat:19.07,lng:72.87}]]){u(p,V);console.log(n,'->',out.join(' | '));}
