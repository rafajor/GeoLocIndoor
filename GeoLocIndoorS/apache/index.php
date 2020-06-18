<?php
    $servername = "172.17.0.1";
    $username = "root";
    $password = "ge0";
    $dbname = "GeoLoc";

    $conn = new mysqli($servername, $username, $password, $dbname);

    if ($conn->connect_error) {
        die("Connection failed: " . $conn->connect_error);
    }
    
    $sql = "SELECT session,date FROM GeoLoc.coords GROUP BY session ORDER BY id DESC";
    $result = $conn->query($sql);
    $i=0;
    while($row = $result->fetch_assoc()) {
        $session[$i]['session']=$row['session'];
        $session[$i]['date']=$row['date'];
        $i++;
    }
        
    if(!empty($_GET['s'])){
        $sess=$_GET['s'];
    }
    else{
        $sess=$session[0]['session'];
    }
        
    $sql = "SELECT ip, coordx, coordy FROM GeoLoc.coords WHERE session='".$sess."'";
    $result = $conn->query($sql);
    $i=0;
    $maxx=840; //10-850
    $maxy=590; //0-590
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
    if(($mx/$maxx)<($my/$maxy)){
        $mpp=$my/$maxy;
    }
    else{
        $mpp=$mx/$maxx;
    }
    $amin=$mpp*(-10);
    $amaxx=$mpp*($maxx+10);
    $amaxy=$mpp*($maxy);

?>

<!DOCTYPE html>
<meta charset="utf-8">
<style>
    body {font-family: "Arial";}

    .grid line {
      stroke: lightgrey;
      stroke-opacity: 0.7;
      shape-rendering: crispEdges;
    }

    .grid path {
      stroke-width: 0;
    }

</style>
<body>
<table width="100%">
<tr><td width="160" valign="top">
<form name="chs" action="index.php" method="GET">
<select name="s" onchange="this.form.submit()">
    <?php
    foreach($session as $s) {?>
<option value="<?php echo $s['session'];?>"<?php if($s['session']==$sess){echo " selected";}?>>
            <?php echo $s['date'];?>
        </option>
    <?php }
    ?>
</select>
</form>
</td><td>
<center>
<svg width="900" height="650" style="border:1px solid"></svg>
</center>
</td>
<script src="https://d3js.org/d3.v4.min.js"></script>
<link href="https://fonts.googleapis.com/css?family=Inconsolata" rel="stylesheet">
<script>
    var margin = {top: 25, right: 25, bottom: 25, left: 25},
        width = 900 - margin.left - margin.right,
        height = 650 - margin.top - margin.bottom;
        
        console.log(height);
    
    var svg = d3.select("svg")
    .append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
    .append("g")
      .attr("transform",
            "translate(" + margin.left + "," + margin.top + ")");
    
var x = d3.scaleLinear().domain([<?php echo $amin;?>, <?php echo $amaxx;?>]).range([0, width]);
    svg
      .append("g")
      .attr("transform", "translate(0," + height + ")")
      .call(d3.axisBottom(x));

var y = d3.scaleLinear().domain([<?php echo $amin;?>, <?php echo $amaxy;?>]).range([ height, 0]);
    svg
      .append("g")
      .call(d3.axisLeft(y));

    svg.append("text")
        .attr("text-anchor", "end")
        .attr("x", width+25)
        .attr("y", height + margin.top -5)
        .text("(m)");

    svg.append("text")
        .attr("text-anchor", "end")
        .attr("transform", "rotate(-90)")
        .attr("y", -margin.left+15)
        .attr("x", -margin.top +50)
        .text("(m)")
   
    var color = d3.scaleOrdinal(d3.schemeCategory20);
        
    var simulation = d3.forceSimulation()
        .force("link", d3.forceLink().id(function(d) { return d.id; }))
            .force('charge', d3.forceManyBody()
          .strength(-200)
          .theta(0.8)
          .distanceMax(150)
        )
        .force("center", d3.forceCenter(width / 2, height / 2));

    function make_x_gridlines() {
        return d3.axisBottom(x)
            .ticks(10)
    }

    // gridlines in y axis function
    function make_y_gridlines() {
        return d3.axisLeft(y)
            .ticks(10)
    }

  d3.json("nodes.php?s=<?php echo $sess;?>", function(error, graph) {
    if (error) throw error;

    var link = svg.append("g")
        .style("stroke", "#aaa")
        .style("stroke-width", "2px")
        .attr("class", "links")
        .selectAll("line")
        .data(graph.links)
        .enter().append("line")
        .attr("stroke-width", function(d) { return Math.sqrt(d.value); });

    var node = svg.append("g")
        .attr("class", "nodes")
        .selectAll("circle")
        .data(graph.nodes)
        .enter().append("circle")
        .attr("r", 8)
        .attr("fill", function(d) { return color(d.group); })
        .call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended));
          
    var label = svg.append("g")
        .attr("class", "labels")
        .selectAll("text")
        .data(graph.nodes)
        .enter().append("text")
        .attr("class", "label")
        .text(function(d) { return d.id; });
          
          // add the X gridlines
          svg.append("g")
              .attr("class", "grid")
              .attr("transform", "translate(0," + height + ")")
              .call(make_x_gridlines()
                  .tickSize(-height)
                  .tickFormat("")
              )

          // add the Y gridlines
          svg.append("g")
              .attr("class", "grid")
              .call(make_y_gridlines()
                  .tickSize(-width)
                  .tickFormat("")
              )
    
    node.append("title")
          .text(function(d) { return (d.id+"\nx:"+d.cx+"\ny:"+d.cy); });
          
    link.append("title")
        .text(function(d) { return d.dist; });

    simulation
        .nodes(graph.nodes)
        .on("tick", ticked);

    simulation.force("link")
        .links(graph.links);

    function ticked() {
        link
            .attr("x1", function(d) { return d.source.x; })
            .attr("y1", function(d) { return d.source.y; })
            .attr("x2", function(d) { return d.target.x; })
            .attr("y2", function(d) { return d.target.y; });

        node
            .attr("cx", function(d) { return d.x; })
            .attr("cy", function(d) { return d.y; });
            
        label
            .attr("x", function(d) { return (d.x+5); })
            .attr("y", function (d) { return (d.y-8); })
            .style("font-size", "12px").style("fill", "#333");
    }
  });
  
function dragstarted(d) {
  if (!d3.event.active) simulation.alphaTarget(0.3).restart()
  //d.fx = d.x
  //d.fy = d.y
//  simulation.fix(d);
}

function dragged(d) {
  //d.fx = d3.event.x
  //d.fy = d3.event.y
//  simulation.fix(d, d3.event.x, d3.event.y);
}

function dragended(d) {
  //d.fx = d3.event.x
  //d.fy = d3.event.y
  if (!d3.event.active) simulation.alphaTarget(0);
  //simulation.unfix(d);
}
  
</script>
</body></html>
