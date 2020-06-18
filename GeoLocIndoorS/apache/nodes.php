<?php
header('Content-Type: application/json');
$servername = "172.17.0.1";
$username = "root";
$password = "ge0";
$dbname = "GeoLoc";

$conn = new mysqli($servername, $username, $password, $dbname);

if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

    $maxx=840; //10-850
    $maxy=590; //0-590
    
    
    if(!empty($_GET['s'])){
        $session=$_GET['s'];
    }
    else{
        $sql = "SELECT session FROM GeoLoc.coords GROUP BY session ORDER BY id DESC LIMIT 0,1";
        $result = $conn->query($sql);
        while($row = $result->fetch_assoc()) {
            $session=$row['session'];
        }
    }
    
$sql = "SELECT ip, coordx, coordy FROM GeoLoc.coords WHERE session='".$session."'";
$result = $conn->query($sql);
$i=0;
    $mx=0;
    $my=0;
while($row = $result->fetch_assoc()) {
    $nodes[$i]['ip']=$row["ip"];
    $nodes[$i]['x']=$row["coordx"];
    if($nodes[$i]['x']>$mx){
        $mx=$nodes[$i]['x'];
    }
    $nodes[$i]['y']=$row["coordy"];
    if($nodes[$i]['y']>$my){
        $my=$nodes[$i]['y'];
    }
    $i++;
}
    //$session="5d569946-0993-4496-9694-d26211d1812f";
    $sql = "SELECT ip1, ip2, distance FROM GeoLoc.measures WHERE session='".$session."'";
    $result = $conn->query($sql);
    $i=0;
    while($row = $result->fetch_assoc()) {
        if($row["ip1"]>$row["ip2"]){
            $distt[$i]['ip1']=$row["ip2"];
            $distt[$i]['ip2']=$row["ip1"];
        }
        else{
            $distt[$i]['ip1']=$row["ip1"];
            $distt[$i]['ip2']=$row["ip2"];
        }
        
        $distt[$i]['dist']=$row["distance"];
        $i++;
    }
    $i=0;
    
    array_multisort($distt);
    $n=1;
    foreach($distt as $dis) {
        if($n==1){
            $d=$dis['dist'];
            $n++;
        }
        else{
            $d=round(($d+$dis['dist'])/2,3);
            
            $dists[$i]['ip1']=$dis['ip1'];
            $dists[$i]['ip2']=$dis['ip2'];
            $dists[$i]['dist']=$d;
            $n--;
            $i++;
        }
    }
    
    
    $factorx=$maxx/$mx;
    $factory=$maxy/$my;
    if($factorx>$factory){
        $factor=$factory;
    }
    else{
        $factor=$factorx;
    }
    $espx=(($maxx-($mx*$factor))/2)+10;
    $espy=(($maxy-($my*$factor))/2)+10;
    
     $i=0;
     $jsontext = "{\r\n\"nodes\":[\r\n";
    
    foreach($nodes as $node) {
        $jsontext .= "\t{\"id\": \"".addslashes($node['ip'])."\", \"fx\": ".addslashes($node['x']*$factor+$espx).", \"fy\": ".addslashes(($node['y']*$factor+$espy)*(-1)+600).", \"cx\": ".addslashes(round($node['x'],3)).", \"cy\": ".addslashes(round($node['y'],3))."},\r\n";
        $i++;
    }
     $jsontext = substr_replace($jsontext, '', -3);
     $jsontext .= "\r\n";
     $jsontext .= "],\r\n \"links\":[\r\n";
     foreach($dists as $dist) {
         $jsontext .= "\t{\"source\": \"".addslashes($dist['ip1'])."\", \"target\": \"".addslashes($dist['ip2'])."\", \"dist\": \"".addslashes($dist['dist'])." m\"},\r\n";
     }
    
     $jsontext = substr_replace($jsontext, '', -3);
     $jsontext .= "\r\n";
     $jsontext .= "]}";
     

     echo $jsontext;
     
$conn->close();
?>
