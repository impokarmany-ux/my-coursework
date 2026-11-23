	public void RegisterReplyMessage(uint reqId, Action<IConnection, IMessage> act) { }

	// RVA: 0x1493B8D8 Offset: 0x149378D8 VA: 0x1493B8D8 Slot: 4
	public void Dispose() { }
}

// Namespace: WatcherSDK
public class MessageSerializer : IMessageSerializer // TypeDefIndex: 60686
{
	// Fields
	private const int Mask = -8;
	private const int WordSize = 8;
	private readonly Dictionary<int, Func<WatcherHeader, Stream, IMessage>> _deserializer; // 0x10
	private readonly WatcherConnection _connection; // 0x18

	// Methods

	// RVA: 0x1493B96C Offset: 0x1493796C VA: 0x1493B96C
	public void .ctor(WatcherConnection conn) { }

	// RVA: 0x1493BA30 Offset: 0x14937A30 VA: 0x1493BA30 Slot: 6
	public bool ReadyToDeserialize(Stream s) { }

	// RVA: 0x1493BC4C Offset: 0x14937C4C VA: 0x1493BC4C Slot: 5
	public IMessage Deserialize(Stream s) { }

	// RVA: 0x1493C3FC Offset: 0x149383FC VA: 0x1493C3FC Slot: 4
	public void Serialize(Stream s, IMessage msg) { }

	// RVA: 0x1493C290 Offset: 0x14938290 VA: 0x1493C290 Slot: 8
	public void Decrypt(byte[] data, int offset, int length) { }

	// RVA: 0x1493C844 Offset: 0x14938844 VA: 0x1493C844 Slot: 7
	public void Encrypt(byte[] data, int offset, int length) { }

	// RVA: 0x1493CA48 Offset: 0x14938A48 VA: 0x1493CA48
	public void RegisterDeserializer(int id, Func<WatcherHeader, Stream, IMessage> func) { }

	// RVA: 0x1493CAF0 Offset: 0x14938AF0 VA: 0x1493CAF0
	public static string GetStringMessageBody(WatcherHeader h, Stream s) { }

	// RVA: 0x1493C5AC Offset: 0x149385AC VA: 0x1493C5AC
	private static int FastXorBytes(byte[] data, int index, int length, byte[] mask, int offset) { }

	// RVA: -1 Offset: -1
	public static T Deserialize<T>(int codec, Stream s, int length) { }
	/* GenericInstMethod :
	|
	|-RVA: 0x9062528 Offset: 0x905E528 VA: 0x9062528
	|-MessageSerializer.Deserialize<object>
	|
	|-RVA: 0x9062A94 Offset: 0x905EA94 VA: 0x9062A94
	|-MessageSerializer.Deserialize<__Il2CppFullySharedGenericType>
	*/

	// RVA: 0x1493CC48 Offset: 0x14938C48 VA: 0x1493CC48
	public static void Serialize(Stream s, int codec, object value) { }
}

// Namespace: WatcherSDK
public enum ConnectionType // TypeDefIndex: 60687
{
	// Fields
	public int value__; // 0x0
	public const ConnectionType Tcp = 0;
	public const ConnectionType Udp = 1;
}

// Namespace: WatcherSDK
public class Handshaker : IMessageProcesser // TypeDefIndex: 60688
{
	// Fields
	private WatcherConnection _connection; // 0x10
	public string ConnId; // 0x18
	public string FingerPrint; // 0x20
	public byte[] Mask; // 0x28
	public int RecvEncryptMaskOffset; // 0x30
	public int SendEncryptMaskOffset; // 0x34
	public string ServerId; // 0x38

	// Methods

	// RVA: 0x1493CDF0 Offset: 0x14938DF0 VA: 0x1493CDF0 Slot: 4
	public void Init(IConnection conn) { }

	// RVA: 0x1493CEBC Offset: 0x14938EBC VA: 0x1493CEBC Slot: 5
	public void Process(IConnection conn, IMessage m) { }

	// RVA: 0x1493D7C8 Offset: 0x149397C8 VA: 0x1493D7C8 Slot: 6
	public void Tick(float delta) { }

	// RVA: 0x1493D83C Offset: 0x1493983C VA: 0x1493D83C
	public void .ctor() { }
}

// Namespace: WatcherSDK
public class Heartbeater : IMessageProcesser // TypeDefIndex: 60689
{
	// Fields
	private IConnection _conn; // 0x10
	private readonly float _duration; // 0x18
	private int _waitingPong; // 0x1C
	private float _elapsedSecond; // 0x20
	private float _lastWaitSecond; // 0x24
	private Dictionary<int, float> _waitingTickDic; // 0x28

	// Properties
	public float duration { get; }
	public bool HasHeartbeat { get; }

	// Methods

	// RVA: 0x1493D8A4 Offset: 0x149398A4 VA: 0x1493D8A4
	public float get_duration() { }

	// RVA: 0x1493D908 Offset: 0x14939908 VA: 0x1493D908
	public void .ctor() { }

	// RVA: 0x1493D988 Offset: 0x14939988 VA: 0x1493D988
	public bool get_HasHeartbeat() { }

	// RVA: 0x1493D9F4 Offset: 0x149399F4 VA: 0x1493D9F4 Slot: 4
	public void Init(IConnection conn) { }

	// RVA: 0x1493DA6C Offset: 0x14939A6C VA: 0x1493DA6C Slot: 5
	public void Process(IConnection conn, IMessage m) { }

	// RVA: 0x1493DC5C Offset: 0x14939C5C VA: 0x1493DC5C Slot: 6
	public void Tick(float delta) { }

	// RVA: 0x1493E318 Offset: 0x1493A318 VA: 0x1493E318
	public void Tick() { }

	// RVA: 0x1493E0A4 Offset: 0x1493A0A4 VA: 0x1493E0A4
	private void TickWaitingPong(float delta) { }

	// RVA: 0x1493DFD0 Offset: 0x14939FD0 VA: 0x1493DFD0
	private void CreateWaitCache() { }

	// RVA: 0x1493DB70 Offset: 0x14939B70 VA: 0x1493DB70
	private void SaveWaitPong() { }

	// RVA: 0x1493E4F8 Offset: 0x1493A4F8 VA: 0x1493E4F8
	public float GetPingPongTick() { }
}

// Namespace: WatcherSDK
public class SimpleErrorException : Exception // TypeDefIndex: 60690
{
	// Methods

	// RVA: 0x1493E55C Offset: 0x1493A55C VA: 0x1493E55C
	public void .ctor(string message) { }
}

// Namespace: WatcherSDK
public class WatcherConnection : IConnection, IDisposable // TypeDefIndex: 60691
{
	// Fields
	private readonly IConnection _connection; // 0x10
	private readonly MessageSerializer _serializer; // 0x18
	private readonly IThreadDispatcher _threadDispatcher; // 0x20
	private readonly Handshaker Handshaker; // 0x28
	private readonly Heartbeater Heartbeater; // 0x30
	private readonly ILogger _logger; // 0x38
	[CompilerGenerated]
	private byte <Codec>k__BackingField; // 0x40
	[CompilerGenerated]
	private int <Delay>k__BackingField; // 0x44
	[CompilerGenerated]
	private Action OnConnected; // 0x48
	[CompilerGenerated]
	private Action OnHandshaked; // 0x50
	[CompilerGenerated]
	private Action<bool> OnDisconnected; // 0x58
	[CompilerGenerated]
	private Action<IMessage> OnDataReceived; // 0x60
	[CompilerGenerated]
	private Action<string> OnKickout; // 0x68

	// Properties
	public byte Codec { get; set; }
	public string ConnId { get; }
	public string FingerPrint { get; }
	public string ServerId { get; }
	public int SendEncryptMaskOffset { get; set; }
	public int RecvEncryptMaskOffset { get; set; }
	public byte[] Mask { get; }
	public int Delay { get; set; }
	public bool Connected { get; }
	public IPAddress ResolvedIPAddress { get; }

	// Methods

	// RVA: 0x149390BC Offset: 0x149350BC VA: 0x149390BC
	public void .ctor(string ip, int port, ILogger logger, int codec = 2) { }

	[CompilerGenerated]
	// RVA: 0x1493E600 Offset: 0x1493A600 VA: 0x1493E600
	public byte get_Codec() { }

	[CompilerGenerated]
	// RVA: 0x1493E664 Offset: 0x1493A664 VA: 0x1493E664
	private void set_Codec(byte value) { }

	// RVA: 0x1493E6DC Offset: 0x1493A6DC VA: 0x1493E6DC
	public string get_ConnId() { }

	// RVA: 0x1493E74C Offset: 0x1493A74C VA: 0x1493E74C
	public string get_FingerPrint() { }

	// RVA: 0x1493E7BC Offset: 0x1493A7BC VA: 0x1493E7BC
	public string get_ServerId() { }

	// RVA: 0x1493C954 Offset: 0x14938954 VA: 0x1493C954
	public int get_SendEncryptMaskOffset() { }

	// RVA: 0x1493C9C4 Offset: 0x149389C4 VA: 0x1493C9C4
	public void set_SendEncryptMaskOffset(int value) { }

	// RVA: 0x1493C53C Offset: 0x1493853C VA: 0x1493C53C
	public int get_RecvEncryptMaskOffset() { }

	// RVA: 0x1493C7C0 Offset: 0x149387C0 VA: 0x1493C7C0
	public void set_RecvEncryptMaskOffset(int value) { }

	// RVA: 0x1493C4CC Offset: 0x149384CC VA: 0x1493C4CC
	public byte[] get_Mask() { }

	[CompilerGenerated]
	// RVA: 0x1493E82C Offset: 0x1493A82C VA: 0x1493E82C
	public int get_Delay() { }

	[CompilerGenerated]
	// RVA: 0x1493E890 Offset: 0x1493A890 VA: 0x1493E890
	public void set_Delay(int value) { }

	// RVA: 0x1493E908 Offset: 0x1493A908 VA: 0x1493E908 Slot: 5
	public void Connect(int timeout = 10000) { }

	// RVA: 0x1493E9E4 Offset: 0x1493A9E4 VA: 0x1493E9E4 Slot: 4
	public bool get_Connected() { }

	[CompilerGenerated]
	// RVA: 0x149395B8 Offset: 0x149355B8 VA: 0x149395B8 Slot: 9
	public void add_OnConnected(Action value) { }

	[CompilerGenerated]
	// RVA: 0x1493EACC Offset: 0x1493AACC VA: 0x1493EACC Slot: 10
	public void remove_OnConnected(Action value) { }

	[CompilerGenerated]
	// RVA: 0x14939780 Offset: 0x14935780 VA: 0x14939780
	public void add_OnHandshaked(Action value) { }

	[CompilerGenerated]
	// RVA: 0x1493EBA4 Offset: 0x1493ABA4 VA: 0x1493EBA4
	public void remove_OnHandshaked(Action value) { }

	[CompilerGenerated]
	// RVA: 0x14939690 Offset: 0x14935690 VA: 0x14939690 Slot: 11
	public void add_OnDisconnected(Action<bool> value) { }

	[CompilerGenerated]
	// RVA: 0x1493EC7C Offset: 0x1493AC7C VA: 0x1493EC7C Slot: 12
	public void remove_OnDisconnected(Action<bool> value) { }

	[CompilerGenerated]
	// RVA: 0x149394C8 Offset: 0x149354C8 VA: 0x149394C8 Slot: 13
	public void add_OnDataReceived(Action<IMessage> value) { }

	[CompilerGenerated]
	// RVA: 0x1493ED6C Offset: 0x1493AD6C VA: 0x1493ED6C Slot: 14
	public void remove_OnDataReceived(Action<IMessage> value) { }

	[CompilerGenerated]
	// RVA: 0x1493EE5C Offset: 0x1493AE5C VA: 0x1493EE5C
	public void add_OnKickout(Action<string> value) { }

	[CompilerGenerated]
	// RVA: 0x1493EF4C Offset: 0x1493AF4C VA: 0x1493EF4C
	public void remove_OnKickout(Action<string> value) { }

	// RVA: 0x14939858 Offset: 0x14935858 VA: 0x14939858 Slot: 6
	public void Disconnect() { }

	// RVA: 0x14939E90 Offset: 0x14935E90 VA: 0x14939E90 Slot: 7
	public void Send(IMessage msg) { }

	// RVA: 0x1493F03C Offset: 0x1493B03C VA: 0x1493F03C Slot: 8
	public IPAddress get_ResolvedIPAddress() { }

	// RVA: -1 Offset: -1
	public void RegisterMessage<T>(int msgId) { }
	/* GenericInstMethod :
	|
	|-RVA: 0x915A64C Offset: 0x915664C VA: 0x915A64C
	|-WatcherConnection.RegisterMessage<object>
	*/

	// RVA: 0x1493F108 Offset: 0x1493B108 VA: 0x1493F108
	public void CheckConnection() { }

	// RVA: 0x14939BC8 Offset: 0x14935BC8 VA: 0x14939BC8
	public void Tick(float delta) { }

	// RVA: 0x1493F1FC Offset: 0x1493B1FC VA: 0x1493F1FC
	private void NotifyConnected() { }

	// RVA: 0x1493F274 Offset: 0x1493B274 VA: 0x1493F274
	private void NotifyDataReceived(IMessage s) { }

	// RVA: 0x1493F8C8 Offset: 0x1493B8C8 VA: 0x1493F8C8
	private void NotifyDisconnected(bool connected) { }

	// RVA: 0x1493FA10 Offset: 0x1493BA10 VA: 0x1493FA10 Slot: 15
	public void Dispose() { }

	// RVA: 0x1493FDD0 Offset: 0x1493BDD0 VA: 0x1493FDD0
	public float GetWatcherDelayTime() { }

	[CompilerGenerated]
	// RVA: -1 Offset: -1
	private IMessage <RegisterMessage>b__51_0<T>(WatcherHeader header, Stream stream) { }
	/* GenericInstMethod :
	|
	|-RVA: 0x915A460 Offset: 0x9156460 VA: 0x915A460
	|-WatcherConnection.<RegisterMessage>b__51_0<object>
	*/
}

// Namespace: WatcherSDK
public class CommonMsgFlag // TypeDefIndex: 60692
{
	// Fields
	public const uint CMF_None = 0;
	public const uint CMF_Request = 16777216;
	public const uint CMF_Reply = 33554432;
	public const uint CMF_Encrypted = 67108864;
	public const uint CMF_Packed = 134217728;
	public const uint CMF_HoldOn = 268435456;
	public const uint CMF_Lean = 536870912;

	// Methods

	// RVA: 0x1493FE78 Offset: 0x1493BE78 VA: 0x1493FE78
	public void .ctor() { }
}

// Namespace: WatcherSDK
public enum MsgId // TypeDefIndex: 60693
{
	// Fields
	public int value__; // 0x0
	public const MsgId Invalid = 0;
	public const MsgId Ping = 1;
	public const MsgId Pong = 2;
	public const MsgId Handshake = 3;
	public const MsgId SimpleError = 4;
	public const MsgId Ok = 5;
	public const MsgId Kickout = 6;
}

// Namespace: WatcherSDK
public class CodecType // TypeDefIndex: 60694
{
	// Fields
	public const int AutoFit = 0;
	public const int Protobuf = 1;
	public const int Json = 2;
	public const int MsgPack = 3;

	// Methods

	// RVA: 0x1493D668 Offset: 0x14939668 VA: 0x1493D668
	public static string ToString(int codec) { }

	// RVA: 0x1493FEE0 Offset: 0x1493BEE0 VA: 0x1493FEE0
	public void .ctor() { }
}

// Namespace: WatcherSDK
public class WatcherHeader // TypeDefIndex: 60695
{
	// Fields
	public static readonly int MinSize; // 0x0
	public static readonly uint HashSeed; // 0x4
	public uint Chksum; // 0x10
	public uint CodecAndSize; // 0x14
	private byte Flags; // 0x18
	public uint ComFlagsAndMsgId; // 0x1C
	public byte MulticastN; // 0x20
	public uint N32; // 0x24
	public ulong N64; // 0x28
	public uint ReqId; // 0x30
	public ushort Warden; // 0x34

	// Properties
	public uint MsgId { get; set; }
	public uint ComFlag { get; set; }
	public int PayloadSize { get; set; }
	public byte Codec { get; set; }

	// Methods

	// RVA: 0x1493BBDC Offset: 0x14937BDC VA: 0x1493BBDC
	public static uint GetHeaderSize(uint comFlagsAndMsgID) { }

	// RVA: 0x1493B650 Offset: 0x14937650 VA: 0x1493B650
	public uint get_MsgId() { }

	// RVA: 0x14939D1C Offset: 0x14935D1C VA: 0x14939D1C
	public void set_MsgId(uint value) { }

	// RVA: 0x1493B6B8 Offset: 0x149376B8 VA: 0x1493B6B8
	public uint get_ComFlag() { }

	// RVA: 0x14939E14 Offset: 0x14935E14 VA: 0x14939E14
	public void set_ComFlag(uint value) { }

	// RVA: 0x1493C228 Offset: 0x14938228 VA: 0x1493C228
	public int get_PayloadSize() { }

	// RVA: 0x1493C37C Offset: 0x1493837C VA: 0x1493C37C
	public void set_PayloadSize(int value) { }

	// RVA: 0x1493FF48 Offset: 0x1493BF48 VA: 0x1493FF48
	public byte get_Codec() { }

	// RVA: 0x14939D9C Offset: 0x14935D9C VA: 0x14939D9C
	public void set_Codec(byte value) { }

	// RVA: 0x1493FFAC Offset: 0x1493BFAC VA: 0x1493FFAC
	public static void Serialize(Stream s, WatcherHeader h) { }

	// RVA: 0x1493C070 Offset: 0x14938070 VA: 0x1493C070
	public static WatcherHeader Deserialize(Stream s) { }

	// RVA: 0x1494013C Offset: 0x1493C13C VA: 0x1494013C Slot: 3
	public override string ToString() { }

