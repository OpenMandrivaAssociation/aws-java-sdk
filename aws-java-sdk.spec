Name:		aws-java-sdk
Version:	1.12.780
Release:	1
Summary:	AWS SDK for Java 1.x core, S3, KMS, and STS
Group:		Development/Java
License:	ASL 2.0
URL:		https://github.com/aws/aws-sdk-java
# Tag 1.12.780 (commit fd30f27). The archive is the catalog modules
# plus jmespath-java, which s3, kms, and sts declare. No prebuilt
# jars or class files are included.
Source0:	aws-java-sdk-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	mvn(commons-logging:commons-logging)
BuildRequires:	mvn(commons-codec:commons-codec)
BuildRequires:	mvn(org.apache.httpcomponents:httpclient)
BuildRequires:	mvn(org.apache.httpcomponents:httpcore)
BuildRequires:	mvn(com.fasterxml.jackson.core:jackson-core)
BuildRequires:	mvn(com.fasterxml.jackson.core:jackson-databind)
BuildRequires:	mvn(com.fasterxml.jackson.core:jackson-annotations)
BuildRequires:	mvn(com.fasterxml.jackson.dataformat:jackson-dataformat-cbor)
BuildRequires:	mvn(joda-time:joda-time)
BuildRequires:	apache-commons-logging
BuildRequires:	apache-commons-codec
BuildRequires:	httpcomponents-client
BuildRequires:	httpcomponents-core
BuildRequires:	jackson-core >= 2.23.0
BuildRequires:	jackson-databind >= 2.23.0
BuildRequires:	jackson-annotations >= 2.23
BuildRequires:	jackson-dataformat-cbor >= 2.23.0
BuildRequires:	joda-time
Requires:	jackson-core >= 2.23.0
Requires:	jackson-dataformat-cbor >= 2.23.0

%description
AWS SDK for Java 1.x modules Gradle pins at %{version}: core, S3,
KMS, and STS. jmespath-java from the same tag is included because
those service modules declare it. Compiled with javac against system
Jackson 2.23.0, including jackson-dataformat-cbor 2.23.0, so the
SDK CBOR generator accepts the Jackson jars.

%prep
%autosetup -n aws-java-sdk-%{version}
find . -name '*.jar' -delete
find . -name '*.class' -delete

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH=$JAVA_HOME/bin:$PATH
CP="%{_javadir}/commons-logging.jar:%{_javadir}/commons-codec.jar:%{_javadir}/httpcomponents/httpclient.jar:%{_javadir}/httpcomponents/httpcore.jar:%{_javadir}/jackson-core.jar:%{_javadir}/jackson-databind.jar:%{_javadir}/jackson-annotations.jar:%{_javadir}/joda-time.jar:%{_javadir}/jackson-dataformat-cbor.jar"

compile_mod() {
	name=$1
	extra=$2
	expect=$3
	find "$name/src/main/java" -name '*.java' > "$name.sources"
	test "$(wc -l < "$name.sources")" -eq "$expect"
	mkdir -p "$name-classes"
	javac --release 8 -encoding UTF-8 -Xlint:-options \
		-cp "$CP:$extra" \
		-d "$name-classes" @"$name.sources"
	if [ -d "$name/src/main/resources" ]; then
		/bin/cp -a "$name/src/main/resources/." "$name-classes/"
	fi
	jar cf "$name.jar" -C "$name-classes" .
}

compile_mod jmespath-java "" 28
compile_mod aws-java-sdk-core "" 596
compile_mod aws-java-sdk-kms "jmespath-java.jar:aws-java-sdk-core.jar" 438
compile_mod aws-java-sdk-sts "jmespath-java.jar:aws-java-sdk-core.jar" 87
compile_mod aws-java-sdk-s3 "jmespath-java.jar:aws-java-sdk-core.jar:aws-java-sdk-kms.jar" 683
javap -v -classpath aws-java-sdk-core.jar com.amazonaws.util.VersionInfoUtils | grep -q 'major version: 52'

dep() {
	echo "    <dependency>"
	echo "      <groupId>$1</groupId>"
	echo "      <artifactId>$2</artifactId>"
	echo "      <version>$3</version>"
	echo "    </dependency>"
}

write_pom() {
	artifact=$1
	shift
	{
		echo '<?xml version="1.0" encoding="UTF-8"?>'
		echo '<project xmlns="http://maven.apache.org/POM/4.0.0">'
		echo '  <modelVersion>4.0.0</modelVersion>'
		echo '  <groupId>com.amazonaws</groupId>'
		echo "  <artifactId>${artifact}</artifactId>"
		echo '  <version>%{version}</version>'
		echo "  <name>${artifact}</name>"
		echo '  <description>AWS SDK for Java %{version}, built from source against system libraries.</description>'
		echo '  <url>https://github.com/aws/aws-sdk-java</url>'
		echo '  <licenses>'
		echo '    <license>'
		echo '      <name>Apache License, Version 2.0</name>'
		echo '      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>'
		echo '    </license>'
		echo '  </licenses>'
		if [ "$#" -gt 0 ]; then
			echo '  <dependencies>'
			while [ "$#" -gt 0 ]; do
				dep "$1" "$2" "$3"
				shift 3
			done
			echo '  </dependencies>'
		fi
		echo '</project>'
	} > "$artifact.pom"
}

write_pom jmespath-java \
	com.fasterxml.jackson.core jackson-databind 2.23.0 \
	com.fasterxml.jackson.core jackson-core 2.23.0 \
	com.fasterxml.jackson.core jackson-annotations 2.23
write_pom aws-java-sdk-core \
	commons-logging commons-logging 1.4.0 \
	commons-codec commons-codec 1.23.0 \
	org.apache.httpcomponents httpclient 4.5.14 \
	org.apache.httpcomponents httpcore 4.4.16 \
	com.fasterxml.jackson.core jackson-databind 2.23.0 \
	com.fasterxml.jackson.core jackson-core 2.23.0 \
	com.fasterxml.jackson.core jackson-annotations 2.23 \
	com.fasterxml.jackson.dataformat jackson-dataformat-cbor 2.23.0 \
	joda-time joda-time 2.15.1
write_pom aws-java-sdk-kms \
	com.amazonaws aws-java-sdk-core %{version} \
	com.amazonaws jmespath-java %{version}
write_pom aws-java-sdk-sts \
	com.amazonaws aws-java-sdk-core %{version} \
	com.amazonaws jmespath-java %{version}
write_pom aws-java-sdk-s3 \
	com.amazonaws aws-java-sdk-kms %{version} \
	com.amazonaws aws-java-sdk-core %{version} \
	com.amazonaws jmespath-java %{version}

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH=$JAVA_HOME/bin:$PATH
CP="%{_javadir}/commons-logging.jar:%{_javadir}/commons-codec.jar:%{_javadir}/httpcomponents/httpclient.jar:%{_javadir}/httpcomponents/httpcore.jar:%{_javadir}/jackson-core.jar:%{_javadir}/jackson-databind.jar:%{_javadir}/jackson-annotations.jar:%{_javadir}/joda-time.jar:%{_javadir}/jackson-dataformat-cbor.jar:jmespath-java.jar:aws-java-sdk-core.jar:aws-java-sdk-kms.jar:aws-java-sdk-sts.jar:aws-java-sdk-s3.jar"
cat > CheckAws.java <<'END'
package com.amazonaws.protocol.json;

import com.amazonaws.jmespath.JmesPathEvaluationVisitor;
import com.amazonaws.jmespath.JmesPathField;
import com.amazonaws.jmespath.ObjectMapperSingleton;
import com.amazonaws.services.kms.model.CreateKeyRequest;
import com.amazonaws.services.s3.AmazonS3URI;
import com.amazonaws.services.s3.model.GetObjectRequest;
import com.amazonaws.services.securitytoken.model.GetCallerIdentityRequest;
import com.amazonaws.util.VersionInfoUtils;
import com.fasterxml.jackson.databind.JsonNode;

public class CheckAws {
    public static void main(String[] args) throws Exception {
        String version = VersionInfoUtils.getVersion();
        AmazonS3URI uri = new AmazonS3URI("s3://gradle-bucket/object-key");
        GetObjectRequest get = new GetObjectRequest(uri.getBucket(), uri.getKey());
        CreateKeyRequest key = new CreateKeyRequest().withDescription("gradle");
        GetCallerIdentityRequest id = new GetCallerIdentityRequest();
        JsonNode input = ObjectMapperSingleton.getObjectMapper().readTree("{\"n\":40}");
        JsonNode out = new JmesPathField("n").accept(new JmesPathEvaluationVisitor(), input);
        StructuredJsonGenerator gen = SdkStructuredCborFactory.SDK_CBOR_FACTORY.createWriter("application/cbor");
        gen.writeStartObject();
        gen.writeFieldName("n");
        gen.writeValue(40);
        gen.writeEndObject();
        byte[] cbor = gen.getBytes();
        System.out.println("aws_ok " + version + " " + get.getBucketName() + " " + get.getKey() + " " + key.getDescription() + " " + id.getClass().getSimpleName() + " " + out.asInt() + " " + cbor.length);
    }
}
END
javac --release 8 -encoding UTF-8 -Xlint:-options -cp "$CP" -d check-classes CheckAws.java
java -cp "check-classes:$CP" com.amazonaws.protocol.json.CheckAws > check.log
cat check.log
grep -F -q 'aws_ok %{version} gradle-bucket object-key gradle GetCallerIdentityRequest 40 6' check.log

%install
# No -u: rpm's install trailer reads DONT_CLEANUP, which is unset.
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact jmespath-java.pom:jmespath-java.jar \
	--file-name jmespath-java \
	--filelist .mfiles
for name in aws-java-sdk-core aws-java-sdk-kms aws-java-sdk-sts aws-java-sdk-s3
do
	sysjar install --buildroot %{buildroot} \
		--artifact "$name.pom:$name.jar" \
		--file-name "$name" \
		--filelist ".mfiles-$name"
	grep -v '%%dir /usr/share/sysjar/index/com.amazonaws' ".mfiles-$name" >> .mfiles
done

%files -f .mfiles
%license LICENSE.txt
%doc NOTICE.txt README.md
