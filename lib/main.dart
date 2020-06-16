import 'dart:core';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:personalapp/complete.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(

      theme: ThemeData(
        brightness: Brightness.dark,
        primarySwatch: Colors.yellow,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: MyHomePage(),
    );
  }
}

class MyHomePage extends StatefulWidget {

  @override
  _MyHomePageState createState() => _MyHomePageState();
}
class _MyHomePageState extends State<MyHomePage> {

  final database = Firestore.instance;
  final GlobalKey<NavigatorState> navigatorKey = new GlobalKey<NavigatorState>();
  final GlobalKey<ScaffoldState> _scaffold = new GlobalKey<ScaffoldState>();

  Widget _card(bool comp,DocumentSnapshot doc){
    if(comp){
      return new Card(
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20.0)
        ),
        color: Colors.green,
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(mainAxisSize: MainAxisSize.max,
              children: [
                Expanded(child: Text(doc['task'].toString(),style: TextStyle(fontSize: 20,),)),
                Icon(Icons.check,size: 25,color: Colors.white,)
              ]),
        ),
      );
    }
    else
      return SizedBox(height: 0,);
  }
  Widget _card1(bool comp,DocumentSnapshot doc){
    if(!comp){
      return new Card(
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20.0)
        ),
        color: Colors.amber,
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(mainAxisSize: MainAxisSize.max,
              children: [
                Expanded(child: Text(doc['task'].toString(),style: TextStyle(fontSize: 20,),)),
                Icon(Icons.check,size: 25,color: Colors.white,)
              ]),
        ),
      );
    }
    else
      return SizedBox(height: 0,);
  }


  @override
  Widget build(BuildContext context) {
    return SafeArea(
        child: DefaultTabController(
          length: 2,
          child: Scaffold(

            key: _scaffold,

            appBar: AppBar(backgroundColor: Colors.blueAccent,
            bottom: TabBar(
              tabs: [
                Tab(icon: Icon(Icons.access_time),),
                Tab(icon: Icon(Icons.check),),
              ],
            ),
            title: Text("TODO",style: TextStyle(fontSize: 25,fontWeight: FontWeight.bold),),
            centerTitle: true,),
            body: TabBarView(
              children: <Widget>[
                Scaffold(
                  floatingActionButton: FloatingActionButton(backgroundColor: Colors.orange,child: Icon(Icons.add),onPressed: (){},),
                  body: StreamBuilder<QuerySnapshot>(
                    stream: database.collection("todo").snapshots(),
                    builder: (BuildContext context, AsyncSnapshot<QuerySnapshot> snapshot){
                      if(snapshot.hasError)
                        return Text("Error: ${snapshot.error}");
                      switch (snapshot.connectionState){
                        case ConnectionState.waiting : return Center(child: new CircularProgressIndicator(backgroundColor: Colors.white,));
                        default:
                          return new ListView(
                            children: snapshot.data.documents.map((DocumentSnapshot doc){
                              return Padding(
                                padding: const EdgeInsets.all(8.0),
                                child: _card1(doc["completed"], doc),
                              );
                            }).toList(),
                          );
                      }
                    },
                  ),
                ),
                StreamBuilder<QuerySnapshot>(
                  stream: database.collection("todo").snapshots(),
                  builder: (BuildContext context, AsyncSnapshot<QuerySnapshot> snapshot){
                    if(snapshot.hasError)
                      return Text("Error: ${snapshot.error}");
                    switch (snapshot.connectionState){
                      case ConnectionState.waiting : return Center(child: new CircularProgressIndicator(backgroundColor: Colors.white,));
                      default:
                        return new ListView(
                          children: snapshot.data.documents.map((DocumentSnapshot doc){
                            return Padding(
                              padding: const EdgeInsets.all(8.0),
                              child: _card(doc["completed"], doc),
                            );
                          }).toList(),
                        );
                    }
                  },
                ),
              ],
            )

          ),
        ),

    );
  }
}
